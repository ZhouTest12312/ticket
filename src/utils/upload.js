import OSS from 'ali-oss';
import moment from 'moment';

const env = process.env.NODE_ENV;

let expirationTime = null; // STS token 过期时间
let client = null; // OSS Client 实例

const bucket = {
  development: 'filesdev',
  dev: 'filesdev',
  pre: 'filespre',
  beta: 'filespro',
  production: 'filespro'
};

// 初始化 oss client
export function initOssClient(
  accessKeyId,
  accessKeySecret,
  stsToken,
  expiration,
  bucketName
) {
  client = new OSS({
    accessKeyId: accessKeyId.toString(),
    accessKeySecret: accessKeySecret.toString(),
    stsToken: stsToken.toString(),
    region: 'oss-cn-shanghai',
    bucket: bucketName
  });
  expirationTime = expiration;
  return client;
}

// 检查 oss 实例以及过期时间
export function checkOssClient() {
  const current = moment();
  return moment(expirationTime).diff(current) < 0 ? null : client;
}

// 用于 sts token 失效、用户登出时注销 oss client
export function destroyOssClient() {
  client = null;
}
