import { useMemo, useState } from "react";

import { inputClass } from "@/components/form";
import { useTopics } from "@/hooks/useTopics";

export default function TopicsPage() {
  const { data: topics, isPending, isError, error } = useTopics();
  const [category, setCategory] = useState("");

  const names = useMemo(() => new Map((topics ?? []).map((t) => [t.slug, t.name])), [topics]);
  const categories = useMemo(
    () => [...new Set((topics ?? []).map((t) => t.category))].sort(),
    [topics],
  );
  const visible = (topics ?? []).filter((t) => category === "" || t.category === category);

  return (
    <section>
      <h1 className="text-xl font-semibold text-neutral-900">Topics</h1>
      <p className="mt-1 mb-4 text-neutral-500">The DSA catalog, in study order.</p>

      {isPending && <p className="text-neutral-500">Loading…</p>}
      {isError && <p className="text-red-600">Could not load topics: {error.message}</p>}

      {topics && topics.length === 0 && (
        <div className="rounded-md border border-dashed border-neutral-300 bg-white p-6 text-neutral-600">
          No topics yet. Run <code className="rounded bg-neutral-100 px-1">make seed</code>.
        </div>
      )}

      {topics && topics.length > 0 && (
        <>
          <div className="mb-3 flex items-center gap-2">
            <label htmlFor="category" className="text-xs font-medium text-neutral-700">
              Category
            </label>
            <select
              id="category"
              className={`${inputClass} w-auto`}
              value={category}
              onChange={(e) => setCategory(e.target.value)}
            >
              <option value="">All categories</option>
              {categories.map((c) => (
                <option key={c} value={c}>
                  {c}
                </option>
              ))}
            </select>
            <span className="text-xs text-neutral-500">{visible.length} topics</span>
          </div>
          <div className="overflow-x-auto rounded-md border border-neutral-200 bg-white">
            <table className="min-w-full text-left text-sm">
              <thead className="bg-neutral-50 text-xs text-neutral-600">
                <tr>
                  <th className="px-3 py-2 font-medium">#</th>
                  <th className="px-3 py-2 font-medium">Name</th>
                  <th className="px-3 py-2 font-medium">Slug</th>
                  <th className="px-3 py-2 font-medium">Category</th>
                  <th className="px-3 py-2 font-medium">Tier</th>
                  <th className="px-3 py-2 text-right font-medium">Problems</th>
                  <th className="px-3 py-2 text-right font-medium">Min/problem</th>
                  <th className="px-3 py-2 text-right font-medium">Est. hours</th>
                  <th className="px-3 py-2 font-medium">Prerequisites</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-100">
                {visible.map((t) => (
                  <tr key={t.slug}>
                    <td className="px-3 py-2 text-neutral-500">{t.order_index}</td>
                    <td className="px-3 py-2 font-medium text-neutral-900">{t.name}</td>
                    <td className="px-3 py-2 font-mono text-xs text-neutral-500">{t.slug}</td>
                    <td className="px-3 py-2">{t.category}</td>
                    <td className="px-3 py-2">{t.difficulty_tier}</td>
                    <td className="px-3 py-2 text-right">{t.default_problem_count}</td>
                    <td className="px-3 py-2 text-right">{t.est_minutes_per_problem}</td>
                    <td className="px-3 py-2 text-right">
                      {((t.default_problem_count * t.est_minutes_per_problem) / 60).toFixed(1)}
                    </td>
                    <td className="px-3 py-2">
                      <div className="flex flex-wrap gap-1">
                        {t.prerequisites.map((slug) => (
                          <span
                            key={slug}
                            className="rounded-full bg-neutral-100 px-2 py-0.5 text-xs text-neutral-700"
                          >
                            {names.get(slug) ?? slug}
                          </span>
                        ))}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </>
      )}
    </section>
  );
}
