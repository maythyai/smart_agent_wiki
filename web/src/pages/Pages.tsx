import { useState } from 'react';
import { useNavigate } from 'react-router';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../lib/api';
import type { PageResponse, PageStatus } from '../types/api';
import EntityTypeBadge from '../components/entity/EntityTypeBadge';
import { useEntityTypes } from '../hooks/useEntityTypes';

interface PagesListResponse {
  pages: PageResponse[];
  total: number;
}

/**
 * Pages list page — 断裂点 #2 fix.
 * Shows all wiki pages with search, and provides "New Page" entry.
 */
export default function Pages() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [search, setSearch] = useState('');
  const [entityTypeFilter, setEntityTypeFilter] = useState<string>('');
  const [showNewForm, setShowNewForm] = useState(false);
  const [newTitle, setNewTitle] = useState('');
  const [newContent, setNewContent] = useState('');

  const { data: entityTypes } = useEntityTypes();

  // Fetch pages list
  const { data, isLoading, error } = useQuery<PagesListResponse>({
    queryKey: ['pages', search, entityTypeFilter],
    queryFn: () =>
      api.get<PagesListResponse>('/api/pages', {
        q: search || undefined,
        entity_type: entityTypeFilter || undefined,
      }),
    staleTime: 30_000,
  });

  // Create page mutation
  const createMutation = useMutation<PageStatus, Error, { title: string; content: string; slug: string }>({
    mutationFn: (data) =>
      api.post<PageStatus>('/api/pages', {
        slug: data.slug,
        title: data.title,
        content: data.content,
      }),
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({ queryKey: ['pages'] });
      setShowNewForm(false);
      setNewTitle('');
      setNewContent('');
      navigate(`/page/${variables.slug}`);
    },
  });

  const slugify = (text: string) =>
    text.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');

  const handleCreate = () => {
    if (!newTitle.trim()) return;
    createMutation.mutate({
      title: newTitle.trim(),
      content: newContent || `# ${newTitle.trim()}\n\n`,
      slug: slugify(newTitle.trim()),
    });
  };

  const pages = data?.pages ?? [];

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white">
          所有页面
        </h1>
        <button
          onClick={() => setShowNewForm(!showNewForm)}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium
            flex items-center gap-2"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          新建页面
        </button>
      </div>

      {/* New Page Form */}
      {showNewForm && (
        <div className="bg-white dark:bg-gray-800 rounded-lg border dark:border-gray-700 p-4 mb-6">
          <h2 className="text-lg font-semibold mb-3 text-gray-900 dark:text-white">新建页面</h2>
          <div className="space-y-3">
            <input
              type="text"
              value={newTitle}
              onChange={(e) => setNewTitle(e.target.value)}
              placeholder="页面标题"
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                dark:bg-gray-700 dark:border-gray-600 dark:text-white"
            />
            <textarea
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              placeholder="页面内容 (Markdown)"
              rows={6}
              className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
                dark:bg-gray-700 dark:border-gray-600 dark:text-white font-mono text-sm"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={!newTitle.trim() || createMutation.isPending}
                className="px-4 py-2 bg-green-600 hover:bg-green-700 disabled:opacity-50
                  text-white rounded-lg font-medium"
              >
                {createMutation.isPending ? '创建中...' : '创建'}
              </button>
              <button
                onClick={() => {
                  setShowNewForm(false);
                  setNewTitle('');
                  setNewContent('');
                }}
                className="px-4 py-2 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700
                  dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg"
              >
                取消
              </button>
            </div>
            {createMutation.isError && (
              <p className="text-sm text-red-600">
                创建失败: {createMutation.error.message}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Search + Entity Type Filter */}
      <div className="mb-4 space-y-2">
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="搜索页面..."
          className="w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500
            dark:bg-gray-800 dark:border-gray-700 dark:text-white dark:placeholder-gray-400"
        />
        {entityTypes && entityTypes.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            <button
              onClick={() => setEntityTypeFilter('')}
              className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                !entityTypeFilter
                  ? 'bg-indigo-600 text-white'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
              }`}
            >
              全部
            </button>
            {entityTypes.map((t) => (
              <button
                key={t.id}
                onClick={() => setEntityTypeFilter(entityTypeFilter === t.id ? '' : t.id)}
                className={`px-2.5 py-1 text-xs rounded-full transition-colors ${
                  entityTypeFilter === t.id
                    ? 'text-white'
                    : 'bg-gray-100 text-gray-600 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300'
                }`}
                style={
                  entityTypeFilter === t.id
                    ? { backgroundColor: t.color }
                    : undefined
                }
              >
                {t.icon} {t.name}
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="animate-pulse space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-gray-200 dark:bg-gray-700 rounded-lg" />
          ))}
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-600 dark:text-red-400">加载失败: {error.message}</p>
        </div>
      )}

      {/* Pages List */}
      {!isLoading && !error && (
        <div className="space-y-2">
          {pages.length === 0 ? (
            <div className="text-center py-12 text-gray-500 dark:text-gray-400">
              <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
              </svg>
              <p className="text-lg font-medium">还没有页面</p>
              <p className="mt-1">点击"新建页面"创建你的第一个 Wiki 页面</p>
            </div>
          ) : (
            pages.map((page) => (
              <button
                key={page.slug}
                onClick={() => navigate(`/page/${page.slug}`)}
                className="w-full text-left p-4 bg-white dark:bg-gray-800 rounded-lg border
                  dark:border-gray-700 hover:border-blue-300 dark:hover:border-blue-600
                  hover:shadow-sm transition-all"
              >
                <div className="flex items-center justify-between">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <EntityTypeBadge typeId={page.entity_type} />
                      <h3 className="font-semibold text-gray-900 dark:text-white truncate">
                        {page.title}
                      </h3>
                    </div>
                    <p className="text-sm text-gray-500 dark:text-gray-400 mt-1 line-clamp-1">
                      {page.content?.slice(0, 100) || '无内容'}
                    </p>
                  </div>
                  <div className="flex items-center gap-2 text-xs text-gray-400">
                    {page.confidence !== undefined && (
                      <span className="px-2 py-1 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded">
                        置信度 {page.confidence}
                      </span>
                    )}
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </div>
              </button>
            ))
          )}
        </div>
      )}

      {/* Stats */}
      {data && (
        <p className="text-sm text-gray-500 dark:text-gray-400 mt-4 text-center">
          共 {data.total ?? pages.length} 个页面
        </p>
      )}
    </div>
  );
}
