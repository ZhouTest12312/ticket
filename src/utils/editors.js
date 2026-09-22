import TurndownService from 'turndown';
import { marked } from 'marked';

// 创建Turndown实例，用于HTML转Markdown
const turndownService = new TurndownService({
  headingStyle: 'atx',
  hr: '---',
  bulletListMarker: '-',
  codeBlockStyle: 'fenced',
  emDelimiter: '*',
  strongDelimiter: '**',
  linkStyle: 'inlined',
  linkReferenceStyle: 'full'
});

// 配置marked，用于Markdown转HTML
marked.setOptions({
  gfm: true,
  breaks: true,
  smartLists: true,
  smartypants: true
});

export function htmlToMarkdown(html) {
  if (!html) return '';
  return turndownService.turndown(html);
}

export function markdownToHtml(markdown) {
  if (!markdown) return '';
  return marked.parse(markdown);
}
