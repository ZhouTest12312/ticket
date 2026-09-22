/**
 * 将 PRD / Mock / 历史 code 映射为现网字典 dictItemValue。
 * 现网 biz_line 为数字（见 BizLineEnum），term_season 为 *_line 后缀。
 */
const ALIASES_BY_DICT_TYPE = {
  biz_line: {
    PY_GZ: '2',
    PY_CZ: '2',
    peiyou_high: '2',
    senior_peiyou: '2',
    peiyou: '2',
    junior_peiyou: '2',
    primary_peiyou: '5',
    peiyou_suyang: '5',
    competition: '3',
    competition_high: '3',
    competition_literacy: '6',
    sishu: '1',
    online_high: '4',
    online_literacy: '7'
  },
  term_season: {
    autumn: 'autumn_line',
    spring: 'spring_line',
    summer: 'summer_line',
    winter: 'winter_line',
    mini_summer: 'summer_line'
  }
};

/** @param {string} dictType */
export function resolveDictCodeAlias(dictType, code) {
  if (code === null || code === undefined || code === '') return code;
  const text = String(code);
  const map = ALIASES_BY_DICT_TYPE[dictType];
  if (!map) return text;
  return map[text] ?? text;
}
