const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { CleanWebpackPlugin } = require('clean-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');

const copyPaths = [
  { from: path.resolve(__dirname, "src/assets"), to: 'assets' },
];

module.exports = function webpacking(envVariables) {
  let env = envVariables;
  if (!env) {
    env = {};
  }
  if (!env.mode) {
    env.mode = 'production';
  }


  console.log('####################');
  console.log('####################');
  console.log('BUILD bundle with parameters:');
  console.log( env);
  console.log('####################');
  console.log('####################');

  const { mode } = env;
  const devtool = env.mode === 'source-map';


  const output = {
    path: path.resolve(__dirname, 'dist'),
    filename: 'js/[name].[contenthash].js'
  };

  const module = {
    rules: [
      {
        test: /\.(js|jsx)$/,
        exclude: /node_modules/,
        loader: 'babel-loader'
      },
      {
        test: /\.ts|tsx?$/,
        loader: "awesome-typescript-loader"
      },
      {
        test: /\.(css)$/,
        use: [
          {
            loader: "style-loader",
          },
          {
            loader: "css-loader",
          }],
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

    ]
  };

  const resolve = {
    extensions: ['*', '.js', '.json', '.ts', '.tsx', '.jsx'],
    symlinks: false
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
    plugins
  };
};
