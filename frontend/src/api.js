function bridge() {
  if (!window.ordocor) throw new Error('Open OrdoCor from its desktop executable.')
  return window.ordocor
}

export function hasSessionToken() {
  return Boolean(window.ordocor)
}

export async function api(path, options = {}) {
  let body = options.body
  if (typeof body === 'string') body = JSON.parse(body)
  const result = await bridge().invoke(path, { method: options.method || 'GET', body })
  if (!result.ok) {
    const error = new Error(result.error || 'Something went wrong.')
    error.status = result.status || 500
    throw error
  }
  return result.data
}

export function resourceApi(name) {
  return {
    list: (parentId) => api(`/resources/${name}${parentId ? `?parent_id=${parentId}` : ''}`),
    create: (body) => api(`/resources/${name}`, { method: 'POST', body: JSON.stringify(body) }),
    update: (id, body) => api(`/resources/${name}/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
    remove: (id) => api(`/resources/${name}/${id}`, { method: 'DELETE' }),
  }
}

export async function downloadBackup() {
  return api('/backup', { method: 'POST' })
}

export async function openExternal(url) {
  return bridge().openExternal(url)
}
