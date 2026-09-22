import { checkOssClient, initOssClient } from '@/utils/upload';
import AES from '@/utils/aes.js';
import { ElMessage } from 'element-plus';
const getStsToken = () => Promise.reject(new Error('upload api removed'));
let url;
let client = checkOssClient();
let uploadProgress = false;
export function imgUpload(opt) {
  let tmp = opt.file.name.split('.');
  let extname = tmp.pop();
  uploadProgress = true;
  if (client == null) {
    getStsToken()
      .then((res) => {
        let accessKeyId = AES.decrypt(res.data.accessKeyId, '');
        let accessKeySecret = AES.decrypt(res.data.accessKeySecret, '');
        let stsToken = AES.decrypt(res.data.securityToken, '');
        if (res.code == 200) {
          client = initOssClient(
            accessKeyId,
            accessKeySecret,
            stsToken,
            res.data.expiration,
            res.data.bucketName
          );

          // getStsToken().then(res=>{
          // if(res.code==200){
          let randomName = Array(32)
            .fill(null)
            .map(() => Math.round(Math.random() * 16).toString(16))
            .join('');
          let newDate = Date.parse(new Date());
          let fileName = res.data.filePath;
          let filePath = res.data.filePrefix;
          paths = `${fileName}/${randomName}${newDate}.${extname}`;
          console.log(paths, '333333333333333');
          client
            .multipartUpload(paths, opt.file, {
              progress: function (p) {
                const e = {};
                e.progress = Math.floor(p * 100);
                opt.onProgress?.(e);
              }
            })
            .then((res1) => {
              // 统一协议
              if (res1.res.statusCode == 200) {
                uploadProgress = false;
                opt.onSuccess?.({
                  res: res1,
                  url: filePath + paths,
                  name: opt.file.name,
                  type: extname,
                  size: opt.file.size
                });

                return res1;
              } else {
                uploadProgress = false;
                opt.onError?.('上传失败');
              }
            })
            .catch((err) => {
              uploadProgress = false;
              opt.onError?.('上传失败');
              ElMessage.error('上传失败');
              return err;
            });

          // }
          // })
        }
      })
      .catch((err) => {
        opt.onError?.('上传失败');
        ElMessage.error(err?.message || '上传失败');
        return;
      });
  }
  // }else{
  // 生产随机文件名
  let paths = '';
  // let url
  if (client) {
    getStsToken().then((res) => {
      if (res.code == 200) {
        let randomName = Array(32)
          .fill(null)
          .map(() => Math.round(Math.random() * 16).toString(16))
          .join('');
        let newDate = Date.parse(new Date());
        let fileName = res.data.filePath;
        let filePath = res.data.filePrefix;
        paths = `${fileName}/${randomName}${newDate}.${extname}`;
        console.log(filePath, 'filePath');
        client
          .multipartUpload(paths, opt.file, {
            progress: function (p) {
              const e = {};
              e.progress = Math.floor(p * 100);
              uploadProgress = true;
              opt.onProgress?.(e);
            }
          })
          .then(
            (res) => {
              // 统一协议
              if (res.res.statusCode == 200) {
                uploadProgress = false;
                opt.onSuccess?.({
                  res: res,
                  url: filePath + paths,
                  name: opt.file.name,
                  type: extname,
                  size: opt.file.size
                });
                return res;
              } else {
                uploadProgress = false;
                opt.onError?.('上传失败');
              }
            },
            (err) => {
              uploadProgress = false;
              opt.onError?.('上传失败');
              ElMessage.error('上传失败');
              return err;
            }
          );
      }
    });
  }
  // if
}
export function closeUpload() {
  if (uploadProgress == true) {
    return client.cancel();
  }
}
