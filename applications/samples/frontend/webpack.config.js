const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

const copyPaths = [
  { from: path.resolve(__dirname, "src/assets"), to: 'static' },
];

module.exports = function webpacking(envVariables) {
  let env = envVariables;
  if (!env) {
    env = {};
  }
  if (!env.mode) {
    env.mode = 'production';
  }
  if (!env.port) {
    env.devPort = 5000;
  }

  console.log('####################');
  console.log('####################');
  console.log('BUILD bundle with parameters:');
  console.log(env);
  console.log('####################');
  console.log('####################');

  const { mode } = env;
  const devtool = env.mode === 'production' ? undefined :'source-map';


  const output = {
    path: path.resolve(__dirname, 'dist'),
    filename: '[name].[hash].js'
  };

  const module = {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      },
      {
        test: /\.(css)$/,
        loader: ['style-loader', 'css-loader'],
      },
      {
        test: /\.less$/,
        use: [
          {
            loader: "style-loader",
          },
          {
            loader: "css-loader",
          },
          {
            loader: "less-loader",
            options: {
              lessOptions: {
                strictMath: true,
              },
            },
          },
        ],
      },
      {
        test: /\.(png|jpg|gif|eot|woff|woff2|svg|ttf)$/,
        loader: 'file-loader'
      },
      {
        test: /\.ts|tsx?$/,
        loader: "awesome-typescript-loader"
      },
    ]
  };

  const resolve = {
    extensions: ['*', '.js', '.json', '.ts', '.tsx', '.jsx'],
    symlinks: false
  };

  const theDomain = env && env.DOMAIN ? env.DOMAIN : 'localhost' + env.devPort;
  console.log(theDomain);
  const replaceHost = (uri, appName) => uri.replace("__APP_NAME__", appName + '.' + theDomain);
  const proxyTarget = 'http://__APP_NAME__/';

  const devServer = {
    contentBase: path.join(__dirname, 'dist'),
    compress: true,
    port: Number(env.devPort),
    hot: true,
    proxy: {
      '/api': {
        target: replaceHost( proxyTarget, 'checkout'),
        secure: false,
        headers: {
          'X-Current-User-Id': '<put your keycloak user id here>'
        }
      }
    },
    historyApiFallback: true
  };

  const plugins = [
    new CleanWebpackPlugin(),
    new CopyWebpackPlugin({ patterns: copyPaths }),
    new CompressionPlugin(),
    new HtmlWebpackPlugin({
      template: 'src/index.ejs',
      favicon: path.join(__dirname, 'src/assets/icon.png')
    })
  ];

  return {
    mode,
    devtool,
    output,
    module,
    resolve,
    devServer,
    plugins
  };
};
