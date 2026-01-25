#!/usr/bin/env node
/**
 * 跨平台启动 Flask 后端（供 npm run dev 使用）
 * Windows: py -3；Mac/Linux: python3；回退: python
 */
const { spawn } = require('child_process')
const path = require('path')

const script = path.join(__dirname, 'run_web.py')
const isWin = process.platform === 'win32'

const attempts = isWin
  ? [['py', ['-3', script]], ['python', [script]]]
  : [['python3', [script]], ['python', [script]]]

function run([cmd, args]) {
  return new Promise((resolve, reject) => {
    const c = spawn(cmd, args, { stdio: 'inherit', cwd: path.dirname(__dirname) })
    c.on('error', reject)
    c.on('exit', (code, sig) => (code != null ? resolve(code) : reject(sig)))
  })
}

;(async () => {
  for (const a of attempts) {
    try {
      const code = await run(a)
      process.exit(code)
    } catch {
      continue
    }
  }
  console.error('未找到 Python。请安装 Python 并确保在 PATH 中（Windows 可用 py -3）。')
  process.exit(1)
})()
