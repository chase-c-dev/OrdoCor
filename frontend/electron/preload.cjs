const { contextBridge, ipcRenderer } = require('electron')

contextBridge.exposeInMainWorld('ordocor', {
  invoke: (path, options) => ipcRenderer.invoke('ordocor:invoke', path, options),
  openExternal: (url) => ipcRenderer.invoke('ordocor:open-external', url),
})
