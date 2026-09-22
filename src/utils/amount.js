/**
 * 将数字金额转换为中文大写（人民币格式）
 * @param {number|string} num 数字金额，例如 12345.67
 * @returns {string} 中文大写金额
 */
export function amountToChinese(num) {
  const digit = ['零', '壹', '贰', '叁', '肆', '伍', '陆', '柒', '捌', '玖'];
  
  const unit = ['', '拾', '佰', '仟', '万', '拾', '佰', '仟', '亿']; 
  
  const decimal = ['角', '分'];

  // 校验输入是否合法
  if (isNaN(num) || num < 0 || num > 99999999999.99) {
    return '金额错误';
  }

  num = parseFloat(num).toFixed(2); // 保留两位小数
  const [integerPart, decimalPart] = num.split('.');

  let result = '';
  let zeroCount = 0;

  for (let i = 0; i < integerPart.length; i++) {
    const digitIndex = integerPart.length - i - 1;
    const currentDigit = parseInt(integerPart[i]);
    
    if (currentDigit === 0) {
      zeroCount++;
      continue;
    }

    if (zeroCount > 0 && result !== '') {
      result += digit[0];
    }

    result += digit[currentDigit] + (unit[digitIndex] || '');

    zeroCount = 0;
  }

  if (result === '') {
    result = digit[0];
  }

  // 循环结束后，统一加上“元”
  result += '元'; 

  // 处理小数部分（角、分）
  if (decimalPart === '00') {
    result += '整';
  } else {
    for (let i = 0; i < decimalPart.length; i++) {
      const d = parseInt(decimalPart[i]);
      if (d > 0) {
        result += digit[d] + decimal[i];
      }
    }
  }

  return result;
}

/**
 * 安全除法
 * @param {number|string} amount 金额
 * @param {number} divisor 除数
 * @param {number} multiplier 乘数比例
 * @returns {string} 保留两位小数的结果字符串
 */
export function safeDivide(amount, divisor, ratio = 10000) {
  if (divisor === 0) return '0.00';
  const amountInCents = Math.round(parseFloat(amount) * ratio);
  const resultInCents = Math.round(amountInCents / divisor);
  return (resultInCents / ratio).toFixed(2);
}

/**
 * 安全乘法
 */
export function safeMultiply(amount, multiplier, ratio = 10000) {
  const amountInCents = Math.round(parseFloat(amount) * ratio);
  const resultInCents = Math.round(amountInCents * multiplier);
  return (resultInCents / ratio).toFixed(2);
}