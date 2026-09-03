# Capabilities — code-grounded inventory

> Generated from `.csp/code-spec/saw/entry-points.jsonl` (CMS 00-hub distillation).
> Each row traces a capability to its code entry point (file:line).
> `[unverified]` = scenario inferred, not grounded by a real call path —
> do not claim as supported without further verification.

## cli

| capability | entry | file:line | status |
|---|---|---|---|
| cli:audit | audit | src/saw/drivers/cli/commands/audit_cmd.py:17 | [unverified] |
| cli:code-graph | code-graph <sub> | src/saw/code_graph/cli.py:0 | verified |
| cli:compile | compile <sub> | src/saw/drivers/cli/commands/compile_cmd.py:0 | verified |
| cli:conflicts | conflicts | src/saw/drivers/cli/commands/conflicts_cmd.py:18 | [unverified] |
| cli:feed:add | feed add | src/saw/drivers/cli/commands/feed_cmd.py:43 | [unverified] |
| cli:feed:entries | feed entries | src/saw/drivers/cli/commands/feed_cmd.py:217 | [unverified] |
| cli:feed:export | feed export | src/saw/drivers/cli/commands/feed_cmd.py:360 | [unverified] |
| cli:feed:import | feed import | src/saw/drivers/cli/commands/feed_cmd.py:306 | [unverified] |
| cli:feed:info | feed info | src/saw/drivers/cli/commands/feed_cmd.py:264 | [unverified] |
| cli:feed:list | feed list | src/saw/drivers/cli/commands/feed_cmd.py:84 | [unverified] |
| cli:feed:poll | feed poll | src/saw/drivers/cli/commands/feed_cmd.py:137 | [unverified] |
| cli:feed:remove | feed remove | src/saw/drivers/cli/commands/feed_cmd.py:166 | [unverified] |
| cli:feed:update | feed update | src/saw/drivers/cli/commands/feed_cmd.py:187 | [unverified] |
| cli:freshness | freshness | src/saw/drivers/cli/commands/freshness_cmd.py:12 | [unverified] |
| cli:i | i | src/saw/drivers/cli/main.py:0 | [unverified] |
| cli:ingest | ingest | src/saw/drivers/cli/commands/ingest_cmd.py:35 | [unverified] |
| cli:ingest-media | ingest-media | src/saw/drivers/cli/commands/ingest_media_cmd.py:31 | [unverified] |
| cli:init | init | src/saw/drivers/cli/commands/init_cmd.py:22 | [unverified] |
| cli:l | l | src/saw/drivers/cli/main.py:0 | [unverified] |
| cli:lint | lint | src/saw/drivers/cli/commands/lint_cmd.py:12 | [unverified] |
| cli:mcp | mcp | src/saw/drivers/cli/commands/mcp_cmd.py:16 | [unverified] |
| cli:plugin:disable | plugin disable | src/saw/drivers/cli/commands/plugin_cmd.py:97 | [unverified] |
| cli:plugin:enable | plugin enable | src/saw/drivers/cli/commands/plugin_cmd.py:69 | [unverified] |
| cli:plugin:install | plugin install | src/saw/drivers/cli/commands/plugin_cmd.py:43 | [unverified] |
| cli:plugin:list | plugin list | src/saw/drivers/cli/commands/plugin_cmd.py:19 | [unverified] |
| cli:plugin:uninstall | plugin uninstall | src/saw/drivers/cli/commands/plugin_cmd.py:112 | [unverified] |
| cli:q | q | src/saw/drivers/cli/main.py:0 | [unverified] |
| cli:query | query | src/saw/drivers/cli/commands/query_cmd.py:31 | [unverified] |
| cli:review | review | src/saw/drivers/cli/commands/review_cmd.py:13 | [unverified] |
| cli:s | s | src/saw/drivers/cli/main.py:0 | [unverified] |
| cli:search | search | src/saw/drivers/cli/commands/search_cmd.py:24 | [unverified] |
| cli:status | status | src/saw/drivers/cli/commands/status_cmd.py:18 | [unverified] |
| cli:tutorial | tutorial | src/saw/drivers/cli/commands/tutorial_cmd.py:230 | [unverified] |
| cli:v | v | src/saw/drivers/cli/main.py:0 | [unverified] |
| cli:verify | verify | src/saw/drivers/cli/commands/verify_cmd.py:12 | [unverified] |
| cli:w | w | src/saw/drivers/cli/main.py:0 | [unverified] |
| cli:web | web | src/saw/drivers/cli/commands/web_cmd.py:14 | [unverified] |

## mcp

| capability | entry | file:line | status |
|---|---|---|---|
| mcp:saw_architecture | saw_architecture | src/saw/drivers/mcp/tools/code_graph.py:81 | [unverified] |
| mcp:saw_archive | saw_archive | src/saw/drivers/mcp/tools/compile.py:147 | [unverified] |
| mcp:saw_archive_suggest | saw_archive_suggest | src/saw/drivers/mcp/tools/compile.py:168 | [unverified] |
| mcp:saw_audit | saw_audit | src/saw/drivers/mcp/tools/govern.py:211 | [unverified] |
| mcp:saw_backlinks | saw_backlinks | src/saw/drivers/mcp/tools/links.py:147 | [unverified] |
| mcp:saw_blast_radius | saw_blast_radius | src/saw/drivers/mcp/tools/govern.py:249 | [unverified] |
| mcp:saw_challenge | saw_challenge | src/saw/drivers/mcp/tools/thinking.py:30 | [unverified] |
| mcp:saw_code_context | saw_code_context | src/saw/drivers/mcp/tools/code_graph.py:132 | [unverified] |
| mcp:saw_code_query | saw_code_query | src/saw/drivers/mcp/tools/code_graph.py:30 | [unverified] |
| mcp:saw_code_search | saw_code_search | src/saw/drivers/mcp/tools/code_graph.py:56 | [unverified] |
| mcp:saw_code_wiki_generate | saw_code_wiki_generate | src/saw/drivers/mcp/tools/compile.py:453 | [unverified] |
| mcp:saw_code_wiki_status | saw_code_wiki_status | src/saw/drivers/mcp/tools/compile.py:482 | [unverified] |
| mcp:saw_compare | saw_compare | src/saw/drivers/mcp/tools/query.py:198 | [unverified] |
| mcp:saw_compile | saw_compile | src/saw/drivers/mcp/tools/query.py:245 | [unverified] |
| mcp:saw_concept_list | saw_concept_list | src/saw/drivers/mcp/tools/compile.py:205 | [unverified] |
| mcp:saw_concept_relate | saw_concept_relate | src/saw/drivers/mcp/tools/compile.py:259 | [unverified] |
| mcp:saw_concept_view | saw_concept_view | src/saw/drivers/mcp/tools/compile.py:227 | [unverified] |
| mcp:saw_conflicts | saw_conflicts | src/saw/drivers/mcp/tools/govern.py:81 | [unverified] |
| mcp:saw_connect | saw_connect | src/saw/drivers/mcp/tools/thinking.py:37 | [unverified] |
| mcp:saw_context | saw_context | src/saw/drivers/mcp/tools/thinking.py:44 | [unverified] |
| mcp:saw_coverage | saw_coverage | src/saw/drivers/mcp/tools/query.py:281 | [unverified] |
| mcp:saw_cr_create | saw_cr_create | src/saw/drivers/mcp/tools/compile.py:406 | [unverified] |
| mcp:saw_cr_review | saw_cr_review | src/saw/drivers/mcp/tools/compile.py:431 | [unverified] |
| mcp:saw_distill | saw_distill | src/saw/drivers/mcp/tools/learn.py:95 | [unverified] |
| mcp:saw_emerge | saw_emerge | src/saw/drivers/mcp/tools/thinking.py:51 | [unverified] |
| mcp:saw_feedback | saw_feedback | src/saw/drivers/mcp/tools/collaborate.py:89 | [unverified] |
| mcp:saw_flows | saw_flows | src/saw/drivers/mcp/tools/code_graph.py:103 | [unverified] |
| mcp:saw_freshness | saw_freshness | src/saw/drivers/mcp/tools/govern.py:155 | [unverified] |
| mcp:saw_graduate | saw_graduate | src/saw/drivers/mcp/tools/thinking.py:58 | [unverified] |
| mcp:saw_graph | saw_graph | src/saw/drivers/mcp/tools/query.py:156 | [unverified] |
| mcp:saw_graph_overview | saw_graph_overview | src/saw/drivers/mcp/tools/compile.py:289 | [unverified] |
| mcp:saw_impact | saw_impact | src/saw/drivers/mcp/tools/code_graph.py:161 | [unverified] |
| mcp:saw_ingest | saw_ingest | src/saw/drivers/mcp/tools/ingest.py:27 | [unverified] |
| mcp:saw_issue_create | saw_issue_create | src/saw/drivers/mcp/tools/compile.py:346 | [unverified] |
| mcp:saw_issue_list | saw_issue_list | src/saw/drivers/mcp/tools/compile.py:372 | [unverified] |
| mcp:saw_learn | saw_learn | src/saw/drivers/mcp/tools/learn.py:59 | [unverified] |
| mcp:saw_lint | saw_lint | src/saw/drivers/mcp/tools/govern.py:41 | [unverified] |
| mcp:saw_navigate | saw_navigate | src/saw/drivers/mcp/tools/compile.py:307 | [unverified] |
| mcp:saw_outlinks | saw_outlinks | src/saw/drivers/mcp/tools/links.py:197 | [unverified] |
| mcp:saw_page_create | saw_page_create | src/saw/drivers/mcp/tools/pages.py:29 | [unverified] |
| mcp:saw_page_delete | saw_page_delete | src/saw/drivers/mcp/tools/pages.py:147 | [unverified] |
| mcp:saw_page_list | saw_page_list | src/saw/drivers/mcp/tools/pages.py:228 | [unverified] |
| mcp:saw_page_read | saw_page_read | src/saw/drivers/mcp/tools/pages.py:200 | [unverified] |
| mcp:saw_page_update | saw_page_update | src/saw/drivers/mcp/tools/pages.py:87 | [unverified] |
| mcp:saw_query | saw_query | src/saw/drivers/mcp/tools/query.py:45 | [unverified] |
| mcp:saw_reparse | saw_reparse | src/saw/drivers/mcp/tools/ingest.py:75 | [unverified] |
| mcp:saw_review | saw_review | src/saw/drivers/mcp/tools/govern.py:182 | [unverified] |
| mcp:saw_search | saw_search | src/saw/drivers/mcp/tools/query.py:90 | [unverified] |
| mcp:saw_status | saw_status | src/saw/drivers/mcp/tools/learn.py:27 | [unverified] |
| mcp:saw_suggest | saw_suggest | src/saw/drivers/mcp/tools/learn.py:126 | [unverified] |
| mcp:saw_tree_search | saw_tree_search | src/saw/drivers/mcp/tools/query.py:125 | [unverified] |
| mcp:saw_verify | saw_verify | src/saw/drivers/mcp/tools/govern.py:116 | [unverified] |
| mcp:saw_wiki_compile | saw_wiki_compile | src/saw/drivers/mcp/tools/compile.py:44 | [unverified] |
| mcp:saw_wiki_index | saw_wiki_index | src/saw/drivers/mcp/tools/compile.py:70 | [unverified] |
| mcp:saw_wiki_link | saw_wiki_link | src/saw/drivers/mcp/tools/links.py:29 | [unverified] |
| mcp:saw_wiki_lint | saw_wiki_lint | src/saw/drivers/mcp/tools/compile.py:187 | [unverified] |
| mcp:saw_wiki_log | saw_wiki_log | src/saw/drivers/mcp/tools/compile.py:119 | [unverified] |
| mcp:saw_wiki_page | saw_wiki_page | src/saw/drivers/mcp/tools/compile.py:90 | [unverified] |
| mcp:saw_wiki_unlink | saw_wiki_unlink | src/saw/drivers/mcp/tools/links.py:89 | [unverified] |
| mcp:saw_wip | saw_wip | src/saw/drivers/mcp/tools/learn.py:167 | [unverified] |
| mcp:saw_workflow | saw_workflow | src/saw/drivers/mcp/tools/collaborate.py:27 | [unverified] |

## web

| capability | entry | file:line | status |
|---|---|---|---|
| web:api/connector_settings.py:130 | get | src/saw/api/connector_settings.py:130 | [unverified] |
| web:api/connector_settings.py:178 | put | src/saw/api/connector_settings.py:178 | [unverified] |
| web:api/connector_settings.py:246 | post | src/saw/api/connector_settings.py:246 | [unverified] |
| web:api/dashboard_stats.py:17 | get | src/saw/api/dashboard_stats.py:17 | [unverified] |
| web:api/feeds.py:194 | get | src/saw/api/feeds.py:194 | [unverified] |
| web:api/feeds.py:241 | post | src/saw/api/feeds.py:241 | [unverified] |
| web:api/feeds.py:291 | get | src/saw/api/feeds.py:291 | [unverified] |
| web:api/feeds.py:325 | put | src/saw/api/feeds.py:325 | [unverified] |
| web:api/feeds.py:377 | delete | src/saw/api/feeds.py:377 | [unverified] |
| web:api/feeds.py:401 | get | src/saw/api/feeds.py:401 | [unverified] |
| web:api/feeds.py:437 | post | src/saw/api/feeds.py:437 | [unverified] |
| web:api/feeds.py:469 | post | src/saw/api/feeds.py:469 | [unverified] |
| web:api/feeds.py:527 | get | src/saw/api/feeds.py:527 | [unverified] |
| web:api/github.py:120 | post | src/saw/api/github.py:120 | [unverified] |
| web:api/github.py:152 | get | src/saw/api/github.py:152 | [unverified] |
| web:api/github.py:186 | patch | src/saw/api/github.py:186 | [unverified] |
| web:api/github.py:219 | delete | src/saw/api/github.py:219 | [unverified] |
| web:api/github.py:249 | get | src/saw/api/github.py:249 | [unverified] |
| web:api/github.py:268 | get | src/saw/api/github.py:268 | [unverified] |
| web:api/github.py:305 | get | src/saw/api/github.py:305 | [unverified] |
| web:api/github.py:89 | get | src/saw/api/github.py:89 | [unverified] |
| web:api/github_webhook.py:119 | get | src/saw/api/github_webhook.py:119 | [unverified] |
| web:api/github_webhook.py:129 | post | src/saw/api/github_webhook.py:129 | [unverified] |
| web:api/github_webhook.py:58 | post | src/saw/api/github_webhook.py:58 | [unverified] |
| web:api/health.py:113 | get | src/saw/api/health.py:113 | [unverified] |
| web:api/health.py:85 | get | src/saw/api/health.py:85 | [unverified] |
| web:api/health.py:96 | get | src/saw/api/health.py:96 | [unverified] |
| web:api/integrations.py:189 | delete | src/saw/api/integrations.py:189 | [unverified] |
| web:api/integrations.py:223 | post | src/saw/api/integrations.py:223 | [unverified] |
| web:api/integrations.py:295 | get | src/saw/api/integrations.py:295 | [unverified] |
| web:api/integrations.py:326 | get | src/saw/api/integrations.py:326 | [unverified] |
| web:api/integrations.py:86 | get | src/saw/api/integrations.py:86 | [unverified] |
| web:api/integrations_ws.py:37 | websocket | src/saw/api/integrations_ws.py:37 | [unverified] |
| web:api/logseq.py:109 | post | src/saw/api/logseq.py:109 | [unverified] |
| web:api/logseq.py:127 | post | src/saw/api/logseq.py:127 | [unverified] |
| web:api/logseq.py:156 | post | src/saw/api/logseq.py:156 | [unverified] |
| web:api/logseq.py:55 | post | src/saw/api/logseq.py:55 | [unverified] |
| web:api/logseq.py:83 | get | src/saw/api/logseq.py:83 | [unverified] |
| web:api/notion.py:107 | post | src/saw/api/notion.py:107 | [unverified] |
| web:api/notion.py:129 | get | src/saw/api/notion.py:129 | [unverified] |
| web:api/notion.py:158 | patch | src/saw/api/notion.py:158 | [unverified] |
| web:api/notion.py:83 | get | src/saw/api/notion.py:83 | [unverified] |
| web:api/notion_sync.py:109 | post | src/saw/api/notion_sync.py:109 | [unverified] |
| web:api/notion_sync.py:141 | get | src/saw/api/notion_sync.py:141 | [unverified] |
| web:api/notion_sync.py:155 | post | src/saw/api/notion_sync.py:155 | [unverified] |
| web:api/notion_sync.py:169 | post | src/saw/api/notion_sync.py:169 | [unverified] |
| web:api/notion_sync.py:182 | post | src/saw/api/notion_sync.py:182 | [unverified] |
| web:api/notion_sync.py:198 | post | src/saw/api/notion_sync.py:198 | [unverified] |
| web:api/notion_sync.py:207 | get | src/saw/api/notion_sync.py:207 | [unverified] |
| web:api/notion_sync.py:218 | post | src/saw/api/notion_sync.py:218 | [unverified] |
| web:api/oauth_callback.py:104 | get | src/saw/api/oauth_callback.py:104 | [unverified] |
| web:api/oauth_callback.py:146 | get | src/saw/api/oauth_callback.py:146 | [unverified] |
| web:api/oauth_callback.py:87 | get | src/saw/api/oauth_callback.py:87 | [unverified] |
| web:api/routes/collaborate.py:230 | post | src/saw/api/routes/collaborate.py:230 | [unverified] |
| web:api/routes/collaborate.py:327 | get | src/saw/api/routes/collaborate.py:327 | [unverified] |
| web:api/routes/collaborate.py:338 | get | src/saw/api/routes/collaborate.py:338 | [unverified] |
| web:api/routes/govern.py:136 | patch | src/saw/api/routes/govern.py:136 | [unverified] |
| web:api/routes/govern.py:165 | get | src/saw/api/routes/govern.py:165 | [unverified] |
| web:api/routes/govern.py:186 | post | src/saw/api/routes/govern.py:186 | [unverified] |
| web:api/routes/govern.py:211 | post | src/saw/api/routes/govern.py:211 | [unverified] |
| web:api/routes/govern.py:236 | post | src/saw/api/routes/govern.py:236 | [unverified] |
| web:api/routes/govern.py:302 | post | src/saw/api/routes/govern.py:302 | [unverified] |
| web:api/routes/govern.py:364 | get | src/saw/api/routes/govern.py:364 | [unverified] |
| web:api/routes/govern.py:83 | get | src/saw/api/routes/govern.py:83 | [unverified] |
| web:api/routes/impact.py:111 | get | src/saw/api/routes/impact.py:111 | [unverified] |
| web:api/routes/impact.py:54 | post | src/saw/api/routes/impact.py:54 | [unverified] |
| web:api/routes/impact.py:82 | get | src/saw/api/routes/impact.py:82 | [unverified] |
| web:api/routes/query_ingest_learn.py:126 | post | src/saw/api/routes/query_ingest_learn.py:126 | [unverified] |
| web:api/routes/query_ingest_learn.py:146 | post | src/saw/api/routes/query_ingest_learn.py:146 | [unverified] |
| web:api/routes/query_ingest_learn.py:186 | get | src/saw/api/routes/query_ingest_learn.py:186 | [unverified] |
| web:api/routes/query_ingest_learn.py:214 | post | src/saw/api/routes/query_ingest_learn.py:214 | [unverified] |
| web:api/routes/query_ingest_learn.py:251 | post | src/saw/api/routes/query_ingest_learn.py:251 | [unverified] |
| web:api/routes/query_ingest_learn.py:306 | post | src/saw/api/routes/query_ingest_learn.py:306 | [unverified] |
| web:api/routes/query_ingest_learn.py:388 | get | src/saw/api/routes/query_ingest_learn.py:388 | [unverified] |
| web:api/routes/query_ingest_learn.py:446 | get | src/saw/api/routes/query_ingest_learn.py:446 | [unverified] |
| web:api/routes/query_ingest_learn.py:462 | put | src/saw/api/routes/query_ingest_learn.py:462 | [unverified] |
| web:api/routes/query_ingest_learn.py:66 | post | src/saw/api/routes/query_ingest_learn.py:66 | [unverified] |
| web:api/routes/query_ingest_learn.py:97 | post | src/saw/api/routes/query_ingest_learn.py:97 | [unverified] |
| web:api/sync.py:131 | post | src/saw/api/sync.py:131 | [unverified] |
| web:api/sync.py:201 | post | src/saw/api/sync.py:201 | [unverified] |
| web:api/sync.py:223 | get | src/saw/api/sync.py:223 | [unverified] |
| web:api/sync.py:79 | get | src/saw/api/sync.py:79 | [unverified] |
| web:api/sync.py:99 | get | src/saw/api/sync.py:99 | [unverified] |
| web:api/webhook_inbound.py:101 | post | src/saw/api/webhook_inbound.py:101 | [unverified] |
| web:api/webhook_inbound.py:66 | get | src/saw/api/webhook_inbound.py:66 | [unverified] |
| web:drivers/web/routes/auth.py:152 | post | src/saw/drivers/web/routes/auth.py:152 | [unverified] |
| web:drivers/web/routes/auth.py:205 | post | src/saw/drivers/web/routes/auth.py:205 | [unverified] |
| web:drivers/web/routes/auth.py:251 | post | src/saw/drivers/web/routes/auth.py:251 | [unverified] |
| web:drivers/web/routes/auth.py:265 | get | src/saw/drivers/web/routes/auth.py:265 | [unverified] |
| web:drivers/web/routes/auth.py:308 | get | src/saw/drivers/web/routes/auth.py:308 | [unverified] |
| web:drivers/web/routes/auth.py:96 | post | src/saw/drivers/web/routes/auth.py:96 | [unverified] |
| web:drivers/web/routes/capture.py:73 | post | src/saw/drivers/web/routes/capture.py:73 | [unverified] |
| web:drivers/web/routes/entity_types.py:15 | get | src/saw/drivers/web/routes/entity_types.py:15 | [unverified] |
| web:drivers/web/routes/entity_types.py:22 | get | src/saw/drivers/web/routes/entity_types.py:22 | [unverified] |
| web:drivers/web/routes/graph.py:149 | get | src/saw/drivers/web/routes/graph.py:149 | [unverified] |
| web:drivers/web/routes/graph.py:31 | get | src/saw/drivers/web/routes/graph.py:31 | [unverified] |
| web:drivers/web/routes/import_md.py:144 | post | src/saw/drivers/web/routes/import_md.py:144 | [unverified] |
| web:drivers/web/routes/import_md.py:63 | post | src/saw/drivers/web/routes/import_md.py:63 | [unverified] |
| web:drivers/web/routes/onboarding.py:30 | get | src/saw/drivers/web/routes/onboarding.py:30 | [unverified] |
| web:drivers/web/routes/onboarding.py:45 | post | src/saw/drivers/web/routes/onboarding.py:45 | [unverified] |
| web:drivers/web/routes/pages.py:116 | get | src/saw/drivers/web/routes/pages.py:116 | [unverified] |
| web:drivers/web/routes/pages.py:151 | put | src/saw/drivers/web/routes/pages.py:151 | [unverified] |
| web:drivers/web/routes/pages.py:204 | patch | src/saw/drivers/web/routes/pages.py:204 | [unverified] |
| web:drivers/web/routes/pages.py:259 | delete | src/saw/drivers/web/routes/pages.py:259 | [unverified] |
| web:drivers/web/routes/pages.py:341 | get | src/saw/drivers/web/routes/pages.py:341 | [unverified] |
| web:drivers/web/routes/pages.py:383 | get | src/saw/drivers/web/routes/pages.py:383 | [unverified] |
| web:drivers/web/routes/pages.py:417 | get | src/saw/drivers/web/routes/pages.py:417 | [unverified] |
| web:drivers/web/routes/pages.py:44 | get | src/saw/drivers/web/routes/pages.py:44 | [unverified] |
| web:drivers/web/routes/pages.py:465 | post | src/saw/drivers/web/routes/pages.py:465 | [unverified] |
| web:drivers/web/routes/search.py:117 | get | src/saw/drivers/web/routes/search.py:117 | [unverified] |
| web:drivers/web/routes/search.py:26 | get | src/saw/drivers/web/routes/search.py:26 | [unverified] |
| web:drivers/web/routes/templates.py:103 | post | src/saw/drivers/web/routes/templates.py:103 | [unverified] |
| web:drivers/web/routes/templates.py:64 | get | src/saw/drivers/web/routes/templates.py:64 | [unverified] |
| web:drivers/web/routes/templates.py:80 | get | src/saw/drivers/web/routes/templates.py:80 | [unverified] |
| web:drivers/web/routes/timeline.py:186 | post | src/saw/drivers/web/routes/timeline.py:186 | [unverified] |
| web:drivers/web/routes/timeline.py:38 | get | src/saw/drivers/web/routes/timeline.py:38 | [unverified] |
| web:drivers/web/routes/websocket.py:31 | websocket | src/saw/drivers/web/routes/websocket.py:31 | [unverified] |

## Summary

- verified: **2**
- unverified: **213** (need call-path grounding)
- total: 215
