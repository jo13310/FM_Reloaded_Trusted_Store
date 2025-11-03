/**
 * FM Reloaded Download Tracking Worker
 *
 * Cloudflare Worker that increments download counts securely.
 * GitHub token is stored in Cloudflare secrets - never exposed to users!
 *
 * Setup Instructions:
 * 1. Create a Cloudflare account (free tier is sufficient)
 * 2. Go to Workers & Pages → Create Worker
 * 3. Copy this code into the worker
 * 4. Add secrets:
 *    - GITHUB_TOKEN: Your GitHub personal access token
 *    - GITHUB_OWNER: jo13310
 *    - GITHUB_REPO: FM_Reloaded_Trusted_Store
 * 5. Deploy to: https://fm-track.fmreloaded.workers.dev (or your custom domain)
 *
 * Features:
 * - Rate limiting (1 increment per IP per mod per hour)
 * - Bot protection via Cloudflare
 * - Secure token storage
 * - Audit logging
 */

export default {
  async fetch(request, env, ctx) {
    // CORS headers for browser requests
    const corsHeaders = {
      'Access-Control-Allow-Origin': '*',
      'Access-Control-Allow-Methods': 'POST, OPTIONS',
      'Access-Control-Allow-Headers': 'Content-Type',
    };

    // Handle CORS preflight
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders });
    }

    // Only accept POST requests
    if (request.method !== 'POST') {
      return new Response('Method not allowed', {
        status: 405,
        headers: corsHeaders
      });
    }

    try {
      // Parse request body
      const { mod_name } = await request.json();

      if (!mod_name || typeof mod_name !== 'string') {
        return new Response(JSON.stringify({ error: 'Missing or invalid mod_name' }), {
          status: 400,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // Rate limiting check using KV storage (if available)
      if (env.RATE_LIMIT_KV) {
        const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
        const rateKey = `rate_${mod_name}_${clientIP}`;
        const recent = await env.RATE_LIMIT_KV.get(rateKey);

        if (recent) {
          return new Response(JSON.stringify({ error: 'Rate limited', retry_after: 3600 }), {
            status: 429,
            headers: { 'Content-Type': 'application/json', ...corsHeaders }
          });
        }

        // Set rate limit for 1 hour
        ctx.waitUntil(env.RATE_LIMIT_KV.put(rateKey, '1', { expirationTtl: 3600 }));
      }

      // Get environment variables
      const GITHUB_TOKEN = env.GITHUB_TOKEN;
      const GITHUB_OWNER = env.GITHUB_OWNER || 'jo13310';
      const GITHUB_REPO = env.GITHUB_REPO || 'FM_Reloaded_Trusted_Store';

      if (!GITHUB_TOKEN) {
        console.error('GITHUB_TOKEN not configured');
        return new Response(JSON.stringify({ error: 'Server configuration error' }), {
          status: 500,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // GitHub API: Get current mods.json
      const fileUrl = `https://api.github.com/repos/${GITHUB_OWNER}/${GITHUB_REPO}/contents/mods.json`;
      const fileResp = await fetch(fileUrl, {
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'User-Agent': 'FM-Reloaded-Tracker/1.0'
        }
      });

      if (!fileResp.ok) {
        console.error('Failed to fetch mods.json:', await fileResp.text());
        return new Response(JSON.stringify({ error: 'Failed to fetch store data' }), {
          status: 502,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      const fileData = await fileResp.json();

      // Decode base64 content
      const contentJson = atob(fileData.content.replace(/\n/g, ''));
      const modsData = JSON.parse(contentJson);

      // Find and increment mod
      let modFound = false;
      for (const mod of modsData.mods || []) {
        if (mod.name === mod_name) {
          mod.downloads = (mod.downloads || 0) + 1;
          modFound = true;
          console.log(`Incremented ${mod_name}: ${mod.downloads - 1} → ${mod.downloads}`);
          break;
        }
      }

      if (!modFound) {
        return new Response(JSON.stringify({ error: 'Mod not found' }), {
          status: 404,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // Encode updated content
      const newContentJson = JSON.stringify(modsData, null, 2) + '\n';
      const newContentBase64 = btoa(newContentJson);

      // Commit back to GitHub
      const commitResp = await fetch(fileUrl, {
        method: 'PUT',
        headers: {
          'Authorization': `token ${GITHUB_TOKEN}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json',
          'User-Agent': 'FM-Reloaded-Tracker/1.0'
        },
        body: JSON.stringify({
          message: `Increment download count: ${mod_name}`,
          content: newContentBase64,
          sha: fileData.sha
        })
      });

      if (!commitResp.ok) {
        const error = await commitResp.text();
        console.error('Failed to commit:', error);
        return new Response(JSON.stringify({ error: 'Failed to update store' }), {
          status: 502,
          headers: { 'Content-Type': 'application/json', ...corsHeaders }
        });
      }

      // Success
      return new Response(JSON.stringify({ success: true, mod_name }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });

    } catch (error) {
      console.error('Worker error:', error);
      return new Response(JSON.stringify({ error: 'Internal server error' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', ...corsHeaders }
      });
    }
  }
};
