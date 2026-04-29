import { useParams } from 'react-router';

export default function Page() {
  const { slug } = useParams<{ slug: string }>();

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Page: {slug}</h2>
      <div className="bg-white rounded-lg border p-4">
        <p className="text-gray-500">Milkdown editor placeholder - coming soon</p>
      </div>
    </div>
  );
}