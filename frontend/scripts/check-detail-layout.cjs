/** Measures the built stock dialog in Electron without accessing user data. */
const { app, BrowserWindow } = require('electron')
const fs = require('node:fs')
const os = require('node:os')
const path = require('node:path')
const assert = require('node:assert/strict')

const temporaryDirectory = fs.mkdtempSync(path.join(os.tmpdir(), 'ordocor-layout-'))
app.setPath('userData', temporaryDirectory)
app.disableHardwareAcceleration()

async function waitFor(window, expression) {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (await window.webContents.executeJavaScript(expression)) return
    await new Promise((resolve) => setTimeout(resolve, 100))
  }
  throw new Error(`Timed out waiting for: ${expression}`)
}

app.whenReady().then(async () => {
  const window = new BrowserWindow({
    show: false, width: 1440, height: 900,
    webPreferences: {
      preload: path.join(__dirname, 'detail-layout-preload.cjs'),
      contextIsolation: true, sandbox: true, backgroundThrottling: false,
    },
  })
  try {
    await window.loadFile(path.join(__dirname, '..', 'dist', 'index.html'))
    await waitFor(window, 'Boolean(document.querySelector(".enter-button"))')
    await window.webContents.executeJavaScript('document.querySelector(".enter-button").click()')
    await waitFor(window, 'Boolean(document.querySelector("aside nav"))')
    await window.webContents.executeJavaScript('document.querySelectorAll("aside nav button")[1].click()')
    await waitFor(window, 'Boolean(document.querySelector(".subtabs"))')
    await window.webContents.executeJavaScript('document.querySelectorAll(".subtabs button")[1].click()')
    await waitFor(window, 'Boolean(document.querySelector("tbody tr"))')
    await window.webContents.executeJavaScript('document.querySelector("tbody tr").dispatchEvent(new MouseEvent("dblclick", { bubbles: true }))')
    await waitFor(window, 'Boolean(document.querySelector(".wide-modal .recharts-surface"))')
    await new Promise((resolve) => setTimeout(resolve, 500))

    for (const [width, height] of [[1920, 1080], [1366, 768], [800, 600], [390, 844]]) {
      window.setContentSize(width, height)
      await waitFor(window, `innerWidth === ${width} && innerHeight === ${height}`)
      await new Promise((resolve) => setTimeout(resolve, 350))
      await window.webContents.executeJavaScript('document.getAnimations().forEach((animation) => { if (animation.effect.getTiming().iterations !== Infinity) animation.finish() })')
      await waitFor(window, `(() => {
        const canvas = document.querySelector('.chart-canvas');
        const chart = canvas.querySelector('.recharts-wrapper');
        return chart && Math.abs(chart.getBoundingClientRect().width - canvas.getBoundingClientRect().width) < 2;
      })()`)
      const dimensions = await window.webContents.executeJavaScript(`(() => {
        const dialog = document.querySelector('.wide-modal');
        const rect = dialog.getBoundingClientRect();
        const chart = document.querySelector('.chart-canvas').getBoundingClientRect();
        return { width: innerWidth, height: innerHeight, x: rect.x, y: rect.y,
          dialogWidth: rect.width, dialogHeight: rect.height,
          rootMounted: dialog.parentElement.parentElement === document.body,
          chartWidth: chart.width, chartHeight: chart.height,
          scrollWidth: dialog.scrollWidth, clientWidth: dialog.clientWidth,
          overflowing: [...dialog.querySelectorAll('*')].filter((element) => {
            const child = element.getBoundingClientRect();
            return child.right > rect.right && getComputedStyle(element).visibility !== 'hidden';
          }).slice(0, 8).map((element) => ({ className: element.getAttribute('class'), width: element.getBoundingClientRect().width })) };
      })()`)
      console.log(JSON.stringify(dimensions))
      assert.equal(dimensions.rootMounted, true)
      assert.ok(dimensions.dialogWidth >= dimensions.width * 0.9)
      assert.ok(dimensions.dialogHeight >= dimensions.height * 0.9)
      assert.ok(Math.abs(dimensions.x - (dimensions.width - dimensions.dialogWidth) / 2) < 2)
      assert.ok(Math.abs(dimensions.y - (dimensions.height - dimensions.dialogHeight) / 2) < 2)
      assert.ok(dimensions.chartWidth > 200 && dimensions.chartHeight > 200)
      assert.deepEqual(dimensions.overflowing, [])
    }
    console.log('DETAIL_LAYOUT_OK')
    app.exit(0)
  } catch (error) {
    console.error(error)
    app.exit(1)
  } finally {
    window.destroy()
  }
}).catch((error) => { console.error(error); app.exit(1) })

app.on('quit', () => fs.rmSync(temporaryDirectory, { recursive: true, force: true }))
