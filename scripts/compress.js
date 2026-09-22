import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import archiver from 'archiver';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// 常见的 Git 安装路径
const commonGitPaths = [
  'C:\\Program Files\\Git\\usr\\bin\\md5sum.exe',
  'C:\\Program Files (x86)\\Git\\usr\\bin\\md5sum.exe',
  'D:\\Program Files\\Git\\usr\\bin\\md5sum.exe',
  'D:\\Program Files (x86)\\Git\\usr\\bin\\md5sum.exe',
  'C:\\software\\Git\\usr\\bin\\md5sum.exe'
];

// 查找 md5sum.exe 的路径
async function findMd5sumPath() {
  try {
    // 首先尝试从 PATH 中查找
    const { stdout } = await execAsync('where md5sum.exe', { shell: true });
    if (stdout.trim()) {
      return stdout.trim();
    }
  } catch (error) {
    // 如果 where 命令失败，继续尝试其他方法
  }

  // 尝试常见的 Git 安装路径
  for (const gitPath of commonGitPaths) {
    if (fs.existsSync(gitPath)) {
      return gitPath;
    }
  }

  // 如果都找不到，尝试查找 Git 安装目录
  try {
    const { stdout } = await execAsync('where git', { shell: true });
    if (stdout.trim()) {
      const gitPath = path.dirname(stdout.trim());
      const possibleMd5sumPath = path.join(gitPath, '..', 'usr', 'bin', 'md5sum.exe');
      if (fs.existsSync(possibleMd5sumPath)) {
        return possibleMd5sumPath;
      }
    }
  } catch (error) {
    // 如果 where git 命令失败，继续尝试其他方法
  }

  throw new Error('无法找到 md5sum.exe，请确保已安装 Git 并添加 Git 的 bin 目录到系统环境变量 PATH 中');
}

// 生成 MD5 校验文件
async function generateMd5File() {
  try {
    // 检查操作系统
    const isWindows = process.platform === 'win32';
    
    if (isWindows) {
      console.log('正在查找 md5sum.exe...');
      const md5sumPath = await findMd5sumPath();
      console.log(`找到 md5sum.exe: ${md5sumPath}`);
      
      console.log('正在生成 MD5 校验文件...');
      const { stdout, stderr } = await execAsync(`"${md5sumPath}" dist.zip > dist.txt`, {
        cwd: path.join(__dirname, '..'),
        shell: true
      });
      
      if (stderr) {
        console.error('生成 MD5 校验文件时出现警告:', stderr);
      }
    } else {
      // Mac 或 Linux 环境
      console.log('正在生成 MD5 校验文件...');
      const { stdout, stderr } = await execAsync('md5 dist.zip | cut -d " " -f 4 > dist.txt', {
        cwd: path.join(__dirname, '..'),
        shell: true
      });
      
      if (stderr) {
        console.error('生成 MD5 校验文件时出现警告:', stderr);
      }
    }
    
    console.log('MD5 校验文件生成完成！');
  } catch (error) {
    console.error('生成 MD5 校验文件失败:', error.message);
    process.exit(1);
  }
}

try {
  console.log('开始压缩...');
  
  // 确保 dist 目录存在
  const distPath = path.join(__dirname, '../dist');
  if (!fs.existsSync(distPath)) {
    console.error('dist 目录不存在，请先运行构建命令');
    process.exit(1);
  }

  // 创建输出文件
  const outputPath = path.join(__dirname, '../dist.zip');
  console.log(`输出文件路径: ${outputPath}`);
  
  const output = fs.createWriteStream(outputPath);
  const archive = archiver('zip', {
    zlib: { level: 9 } // 设置最高压缩级别
  });

  // 监听所有归档数据写入完成
  output.on('close', async () => {
    console.log(`压缩完成！总大小: ${(archive.pointer() / 1024 / 1024).toFixed(2)} MB`);
    await generateMd5File();
  });

  // 监听警告
  archive.on('warning', (err) => {
    if (err.code === 'ENOENT') {
      console.warn('警告:', err);
    } else {
      throw err;
    }
  });

  // 监听错误
  archive.on('error', (err) => {
    console.error('压缩过程中发生错误:', err);
    process.exit(1);
  });

  // 将输出文件与归档器关联
  archive.pipe(output);

  // 添加 dist 目录到归档
  console.log('正在添加文件到压缩包...');
  archive.directory(distPath, false);

  // 完成归档
  console.log('正在完成压缩...');
  await archive.finalize();
  
  console.log('压缩过程完成！');
} catch (error) {
  console.error('发生错误:', error);
  process.exit(1);
} 