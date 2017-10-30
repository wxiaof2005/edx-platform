/* eslint-env node */

'use strict';

var Merge = require('webpack-merge');
var path = require('path');
var webpack = require('webpack');

var commonConfig = require('./webpack.common.config.js');

module.exports = Merge.smart(commonConfig, {
    output: {
        filename: '[name].js'
    },
    devtool: 'source-map',
    plugins: [
        new webpack.LoaderOptionsPlugin({
            debug: true
        }),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify('development')
        })
    ]
});
