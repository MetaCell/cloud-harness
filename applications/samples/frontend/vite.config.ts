import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'



// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Load env file based on `mode` in the current working directory.
  // Set the third parameter to '' to load all env regardless of the `VITE_` prefix.
  const env = loadEnv(mode, process.cwd(), '')

  const theDomain = env && env.DOMAIN ? env.DOMAIN : 'localhost:5000';
  
  console.log('Dev server address: ', theDomain);

  const proxyTarget = theDomain;
  const replaceHost = (uri: string, appName: string) => (uri.includes("samples") && uri.replace("samples", appName + '.' + theDomain)) || uri;


  return {
  plugins: [react()],
  server: {
    port: 9000,
    proxy: {
      '/api/': {
        target: replaceHost( proxyTarget, 'samples'),
        secure: false,
        changeOrigin: true,
      }
  }
}}}
)
