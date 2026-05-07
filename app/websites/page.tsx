'use client'
import { useState } from 'react'
import useSWR from 'swr'
import { api } from '@/lib/api'

export default function WebsitesPage() {
  const { data: websites, mutate } = useSWR('websites', api.listWebsites)
  const [showForm, setShowForm] = useState(false)
  const [form, setForm] = useState({ domain: '', name: '', business_type: '', allowed_domains: '' })
  const [saving, setSaving] = useState(false)
  const [msg, setMsg] = useState('')

  async function handleCreate(e: React.FormEvent) {
    e.preventDefault()
    setSaving(true)
    setMsg('')
    try {
      await api.createWebsite({
        domain: form.domain,
        name: form.name,
        business_type: form.business_type,
        allowed_domains: form.allowed_domains
          ? form.allowed_domains.split(',').map(d => d.trim())
          : [form.domain],
      })
      setMsg('✅ 网站添加成功')
      setShowForm(false)
      setForm({ domain: '', name: '', business_type: '', allowed_domains: '' })
      mutate()
    } catch (err: any) {
      setMsg(`❌ 失败：${err.message}`)
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="p-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">网站管理</h2>
          <p className="text-sm text-gray-500 mt-1">管理所有需要 AI 投放的网站</p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 transition-colors"
        >
          + 添加网站
        </button>
      </div>

      {msg && <p className="mb-4 text-sm">{msg}</p>}

      {showForm && (
        <form onSubmit={handleCreate} className="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-6 space-y-4">
          <h3 className="font-semibold text-gray-900">添加新网站</h3>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-gray-600 mb-1">域名 *</label>
              <input required className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="robotlyne.com"
                value={form.domain} onChange={e => setForm({ ...form, domain: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">网站名称</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="Robotlyne"
                value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">业务类型</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="工业自动化"
                value={form.business_type} onChange={e => setForm({ ...form, business_type: e.target.value })} />
            </div>
            <div>
              <label className="block text-sm text-gray-600 mb-1">允许域名（逗号分隔）</label>
              <input className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm"
                placeholder="robotlyne.com, www.robotlyne.com"
                value={form.allowed_domains} onChange={e => setForm({ ...form, allowed_domains: e.target.value })} />
            </div>
          </div>
          <div className="flex gap-3">
            <button type="submit" disabled={saving}
              className="px-4 py-2 bg-blue-600 text-white text-sm rounded-lg hover:bg-blue-700 disabled:opacity-50">
              {saving ? '保存中...' : '保存'}
            </button>
            <button type="button" onClick={() => setShowForm(false)}
              className="px-4 py-2 bg-gray-100 text-gray-700 text-sm rounded-lg hover:bg-gray-200">
              取消
            </button>
          </div>
        </form>
      )}

      <div className="bg-white rounded-xl shadow-sm border border-gray-100">
        <div className="px-6 py-4 border-b border-gray-100">
          <h3 className="font-semibold text-gray-900">网站列表（{websites?.length ?? 0}）</h3>
        </div>
        <div className="divide-y divide-gray-50">
          {!websites && <p className="px-6 py-8 text-center text-gray-400 text-sm">加载中...</p>}
          {websites?.length === 0 && <p className="px-6 py-8 text-center text-gray-400 text-sm">暂无网站，点击右上角添加</p>}
          {websites?.map((w: any) => (
            <div key={w.id} className="px-6 py-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900">{w.domain}</p>
                  <p className="text-sm text-gray-500 mt-0.5">
                    {w.name && <span>{w.name} · </span>}
                    {w.business_type && <span>{w.business_type} · </span>}
                    <span className="text-xs text-gray-400">ID: {w.id.slice(0, 8)}...</span>
                  </p>
                </div>
                <span className={`px-2 py-1 text-xs rounded-full ${
                  w.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'
                }`}>
                  {w.status === 'active' ? '活跃' : w.status}
                </span>
              </div>
              {w.allowed_domains?.length > 0 && (
                <p className="text-xs text-gray-400 mt-2">
                  允许域名：{w.allowed_domains.join(', ')}
                </p>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
