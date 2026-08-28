import { defineConfig } from '@hey-api/openapi-ts'

export default defineConfig({
  input: '../docs/contracts/openapi.json',
  output: 'src/api/generated',
  plugins: ['@hey-api/typescript'],
})
