const { merge } = require('webpack-merge');
const common = require('./webpack.config.js');

var path = require('path');

const PORT = 9000;


module.exports = env => {

  const theDomain = env && env.DOMAIN ? env.DOMAIN : 'localhost:5000';
  
  console.log('Dev server address: ', theDomain);

  const proxyTarget = theDomain;
  const replaceHost = (uri, appName) => (uri.includes("__APP_NAME__") && uri.replace("__APP_NAME__", appName + '.' + theDomain)) || uri;
  if (!env.port) {
    env.devPort = PORT;
  }


  const devServer = {
    contentBase: path.join(__dirname, 'dist'),
    compress: true,
    port: Number(env.devPort),
    disableHostCheck: true,
    historyApiFallback: true,
    proxy: {
      '/api/': {
        target: replaceHost( proxyTarget, '__APP_NAME__'),
        secure: false,
        changeOrigin: true,
      }
    },
  };

  return merge(
    common(env),
    {
      mode: 'development',
      devtool: 'source-map',
      devServer,
    } 
  )
};
