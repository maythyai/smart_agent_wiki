import { useNavigate } from 'react-router';

/**
 * 404 Not Found page — 断裂点 #5 fix.
 * Friendly page for invalid routes with navigation options.
 */
export default function NotFound() {
  const navigate = useNavigate();

  return (
    <div className="min-h-[60vh] flex items-center justify-center">
      <div className="text-center max-w-md">
        {/* Large 404 */}
        <div className="text-8xl font-bold text-gray-200 dark:text-gray-700 mb-4">
          404
        </div>

        {/* Message */}
        <h1 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
          页面未找到
        </h1>
        <p className="text-gray-500 dark:text-gray-400 mb-8">
          你访问的页面不存在或已被移除。
        </p>

        {/* Actions */}
        <div className="flex items-center justify-center gap-3">
          <button
            onClick={() => navigate('/')}
            className="px-5 py-2.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium"
          >
            返回首页
          </button>
          <button
            onClick={() => navigate('/pages')}
            className="px-5 py-2.5 bg-gray-100 hover:bg-gray-200 dark:bg-gray-700
              dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded-lg font-medium"
          >
            浏览所有页面
          </button>
        </div>

        {/* Search suggestion */}
        <div className="mt-8 p-4 bg-gray-50 dark:bg-gray-800/50 rounded-lg">
          <p className="text-sm text-gray-500 dark:text-gray-400">
            试试用{' '}
            <button
              onClick={() => navigate('/search')}
              className="text-blue-600 dark:text-blue-400 hover:underline font-medium"
            >
              搜索
            </button>{' '}
            找到你需要的内容
          </p>
        </div>
      </div>
    </div>
  );
}
