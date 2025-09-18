// 导入包中所有的文件内容
const modules = import.meta.glob('./**/*.ts', { eager: true })

const exports = {}

for (const path in modules) {
  if (path.includes('index.ts')) continue
  Object.assign(exports, modules[path])
}

export default exports
