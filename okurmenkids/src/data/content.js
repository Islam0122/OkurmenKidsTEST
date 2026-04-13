export const LESSONS = [
  {
    id: 'html-basics',
    title: 'HTML Foundations',
    category: 'HTML',
    icon: '🏗️',
    color: '#fb7185',
    colorDim: 'rgba(251,113,133,0.15)',
    difficulty: 'easy',
    duration: '15 min',
    xp: 20,
    description: 'Build the skeleton of every webpage',
    chapters: [
      {
        id: 'html-1',
        title: 'What is HTML?',
        content: `HTML (HyperText Markup Language) is the standard language for creating web pages. It describes the structure of a page using **elements** represented by tags.

Every HTML document starts with a declaration and has a specific structure:`,
        code: `<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8">
    <title>My First Page</title>
  </head>
  <body>
    <h1>Hello, World!</h1>
    <p>This is my first webpage.</p>
  </body>
</html>`,
        quiz: {
          question: 'What does HTML stand for?',
          options: ['HyperText Markup Language', 'High Tech Modern Language', 'HyperText Modern Layout', 'Hyper Transfer Markup Language'],
          correct: 0,
        },
      },
      {
        id: 'html-2',
        title: 'HTML Elements & Tags',
        content: `HTML elements are the building blocks of a page. Each element has an **opening tag**, **content**, and a **closing tag**.

Common elements include:
- \`<h1>\` to \`<h6>\` — Headings
- \`<p>\` — Paragraphs
- \`<a>\` — Links
- \`<img>\` — Images
- \`<div>\` — Containers`,
        code: `<!-- Headings -->
<h1>Main Title</h1>
<h2>Subtitle</h2>

<!-- Paragraph & link -->
<p>Visit <a href="https://example.com">example.com</a></p>

<!-- Image -->
<img src="photo.jpg" alt="A photo" width="300">

<!-- Container -->
<div class="card">
  <h3>Card Title</h3>
  <p>Card content here</p>
</div>`,
        quiz: {
          question: 'Which tag creates a hyperlink?',
          options: ['<link>', '<href>', '<a>', '<url>'],
          correct: 2,
        },
      },
      {
        id: 'html-3',
        title: 'Forms & Inputs',
        content: `Forms allow users to enter data. The \`<form>\` element wraps input elements and defines where data gets sent.

Key form elements:
- \`<input>\` — Text, email, password, checkbox, radio
- \`<textarea>\` — Multi-line text
- \`<select>\` — Dropdown
- \`<button>\` — Submit or trigger actions`,
        code: `<form action="/submit" method="POST">
  <label for="name">Your Name:</label>
  <input type="text" id="name" name="name" required>

  <label for="email">Email:</label>
  <input type="email" id="email" name="email">

  <label for="level">Level:</label>
  <select id="level" name="level">
    <option value="beginner">Beginner</option>
    <option value="pro">Pro</option>
  </select>

  <button type="submit">Submit</button>
</form>`,
        quiz: {
          question: 'What attribute makes an input required?',
          options: ['mandatory', 'required', 'must', 'needed'],
          correct: 1,
        },
      },
    ],
  },
  {
    id: 'css-flexbox',
    title: 'CSS Flexbox',
    category: 'CSS',
    icon: '📐',
    color: '#38bdf8',
    colorDim: 'rgba(56,189,248,0.15)',
    difficulty: 'medium',
    duration: '20 min',
    xp: 30,
    description: 'Master modern layout techniques',
    chapters: [
      {
        id: 'flex-1',
        title: 'What is Flexbox?',
        content: `Flexbox is a CSS layout method that makes it easy to align and distribute items in a container, even when their sizes are unknown.

Enable flexbox with **display: flex** on the parent container. This makes all direct children into flex items.`,
        code: `.container {
  display: flex;
  /* All children become flex items */
}

/* Basic example */
.nav {
  display: flex;
  gap: 16px;
  align-items: center;
  justify-content: space-between;
}`,
        quiz: {
          question: 'How do you enable flexbox on a container?',
          options: ['flex: true', 'display: flex', 'position: flex', 'layout: flex'],
          correct: 1,
        },
      },
      {
        id: 'flex-2',
        title: 'Justify & Align',
        content: `Two key properties control alignment:

**justify-content** — controls items along the **main axis** (horizontal by default)
**align-items** — controls items along the **cross axis** (vertical by default)

Values: \`flex-start\` | \`flex-end\` | \`center\` | \`space-between\` | \`space-around\``,
        code: `.center-everything {
  display: flex;
  justify-content: center;  /* horizontal */
  align-items: center;      /* vertical */
  height: 100vh;
}

.spread-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
}`,
        quiz: {
          question: 'Which property aligns items along the cross axis?',
          options: ['justify-content', 'align-items', 'flex-align', 'cross-align'],
          correct: 1,
        },
      },
    ],
  },
  {
    id: 'js-fundamentals',
    title: 'JavaScript Basics',
    category: 'JS',
    icon: '⚡',
    color: '#fbbf24',
    colorDim: 'rgba(251,191,36,0.15)',
    difficulty: 'medium',
    duration: '25 min',
    xp: 35,
    description: 'Make your pages interactive and dynamic',
    chapters: [
      {
        id: 'js-1',
        title: 'Variables & Data Types',
        content: `JavaScript has three ways to declare variables: **var** (old), **let** (block-scoped), and **const** (constant).

Core data types:
- **String** — text: \`"hello"\`
- **Number** — integers & decimals: \`42\`, \`3.14\`
- **Boolean** — true/false
- **Array** — ordered list: \`[1, 2, 3]\`
- **Object** — key-value pairs: \`{ name: "Ada" }\``,
        code: `const name = "Ada Lovelace";  // string
let age = 28;                 // number
let isLoggedIn = false;       // boolean

const skills = ["HTML", "CSS", "JS"];  // array
const user = {                          // object
  name: "Ada",
  level: "pro",
  xp: 1200
};

console.log(user.name);      // "Ada"
console.log(skills[0]);      // "HTML"`,
        quiz: {
          question: 'Which keyword creates a constant that cannot be reassigned?',
          options: ['var', 'let', 'const', 'fixed'],
          correct: 2,
        },
      },
      {
        id: 'js-2',
        title: 'Functions & Arrow Functions',
        content: `Functions are reusable blocks of code. Modern JS uses **arrow functions** for cleaner syntax.

Functions can take **parameters** and **return** values.`,
        code: `// Traditional function
function greet(name) {
  return "Hello, " + name + "!";
}

// Arrow function (modern)
const greet = (name) => \`Hello, \${name}!\`;

// Arrow with multiple lines
const calculateXP = (lessons, quests) => {
  const base = lessons * 20;
  const bonus = quests * 50;
  return base + bonus;
};

console.log(greet("Ada"));           // "Hello, Ada!"
console.log(calculateXP(3, 2));      // 160`,
        quiz: {
          question: 'What symbol is used in arrow functions?',
          options: ['-->', '=>', '->', '~>'],
          correct: 1,
        },
      },
    ],
  },
];

export const QUESTS = [
  {
    id: 'flexbox-froggy',
    title: 'Flexbox Froggy',
    icon: '🐸',
    category: 'CSS',
    difficulty: 'easy',
    color: '#4ade80',
    colorDim: 'rgba(74,222,128,0.15)',
    description: 'Help the frogs reach their lily pads using CSS Flexbox',
    xp: 60,
    levels: 5,
    type: 'flexbox',
  },
  {
    id: 'type-racer',
    title: 'Code Typer',
    icon: '⌨️',
    category: 'JS',
    difficulty: 'medium',
    color: '#fbbf24',
    colorDim: 'rgba(251,191,36,0.15)',
    description: 'Type code as fast as you can. Race against the clock!',
    xp: 80,
    levels: 3,
    type: 'typing',
  },
  {
    id: 'selector-duel',
    title: 'CSS Selector Duel',
    icon: '🎯',
    category: 'CSS',
    difficulty: 'medium',
    color: '#38bdf8',
    colorDim: 'rgba(56,189,248,0.15)',
    description: 'Match the correct CSS selector to target elements',
    xp: 70,
    levels: 4,
    type: 'selector',
  },
  {
    id: 'logic-puzzle',
    title: 'JS Logic Puzzles',
    icon: '🧩',
    category: 'JS',
    difficulty: 'hard',
    color: '#a78bfa',
    colorDim: 'rgba(167,139,250,0.15)',
    description: 'Solve JavaScript logic puzzles and debug code snippets',
    xp: 100,
    levels: 6,
    type: 'logic',
  },
];

export const STORIES = [
  {
    id: 'how-web-works',
    title: 'How the Web Works',
    icon: '🌐',
    category: 'Fundamentals',
    readTime: '5 min',
    color: '#4ade80',
    description: 'Browsers, servers, HTTP — what happens when you visit a website',
    content: `# How the Web Works

When you type a URL into your browser, a fascinating chain of events begins.

## 1. DNS Resolution
Your browser asks a **DNS server** to translate the domain (like \`google.com\`) into an IP address (like \`142.250.80.46\`).

## 2. TCP Connection
Your computer establishes a **TCP connection** to the server using a three-way handshake.

## 3. HTTP Request
The browser sends an **HTTP GET request** to the server asking for the page.

## 4. Server Response
The server sends back an **HTTP response** with:
- Status code (\`200 OK\`, \`404 Not Found\`, etc.)
- Headers (content type, caching rules)
- Body (the HTML document)

## 5. Rendering
The browser **parses** the HTML, loads CSS and JavaScript, then **paints** the page on your screen.

This entire process takes milliseconds!`,
  },
  {
    id: 'css-box-model',
    title: 'The CSS Box Model',
    icon: '📦',
    category: 'CSS',
    readTime: '7 min',
    color: '#38bdf8',
    description: 'Every element is a box. Understanding margin, border, padding',
    content: `# The CSS Box Model

Every HTML element is a rectangular **box**. The box model describes how the box is calculated.

## Layers of the Box

\`\`\`
┌─────────────────────────────────────┐
│              MARGIN                 │
│  ┌───────────────────────────────┐  │
│  │           BORDER              │  │
│  │  ┌─────────────────────────┐  │  │
│  │  │        PADDING          │  │  │
│  │  │  ┌───────────────────┐  │  │  │
│  │  │  │     CONTENT       │  │  │  │
│  │  │  └───────────────────┘  │  │  │
│  │  └─────────────────────────┘  │  │
│  └───────────────────────────────┘  │
└─────────────────────────────────────┘
\`\`\`

## box-sizing

By default (\`content-box\`), padding and border are **added** to the width. Use \`border-box\` instead:

\`\`\`css
* {
  box-sizing: border-box; /* Width includes padding + border */
}
\`\`\`

This makes layouts much more predictable!`,
  },
  {
    id: 'js-event-loop',
    title: 'The JavaScript Event Loop',
    icon: '🔄',
    category: 'JavaScript',
    readTime: '10 min',
    color: '#fbbf24',
    description: 'Why JavaScript is single-threaded but handles async so well',
    content: `# The JavaScript Event Loop

JavaScript is **single-threaded** — it can only do one thing at a time. Yet it handles async operations gracefully. How?

## The Call Stack
Functions are pushed onto the **call stack** when called, and popped off when they return.

## Web APIs
When you call \`setTimeout\`, \`fetch\`, or event listeners, the browser handles these in **Web APIs** (outside JS).

## The Queue
When async work completes, callbacks go into the **task queue**.

## The Loop
The event loop constantly checks: *Is the call stack empty?* If yes, it picks the next callback from the queue.

\`\`\`js
console.log("1");           // sync → stack immediately

setTimeout(() => {
  console.log("2");         // async → web API → queue
}, 0);

console.log("3");           // sync → stack immediately

// Output: 1, 3, 2
\`\`\`

This is why \`setTimeout(fn, 0)\` doesn't run immediately!`,
  },
  {
    id: 'responsive-design',
    title: 'Responsive Design Principles',
    icon: '📱',
    category: 'CSS',
    readTime: '8 min',
    color: '#a78bfa',
    description: 'Make your websites look great on all screen sizes',
    content: `# Responsive Design

Responsive design means your site adapts to any screen size — phone, tablet, desktop.

## Mobile-First Approach
Write CSS for small screens first, then add complexity for larger screens.

## Media Queries
\`\`\`css
/* Base styles (mobile) */
.container { padding: 16px; }
.grid { grid-template-columns: 1fr; }

/* Tablet and up */
@media (min-width: 768px) {
  .container { padding: 32px; }
  .grid { grid-template-columns: 1fr 1fr; }
}

/* Desktop */
@media (min-width: 1024px) {
  .grid { grid-template-columns: repeat(3, 1fr); }
}
\`\`\`

## The Viewport Meta Tag
Always add this to your HTML \`<head>\`:
\`\`\`html
<meta name="viewport" content="width=device-width, initial-scale=1">
\`\`\`

Without it, mobile browsers zoom out to fit the full desktop layout.`,
  },
];

export const LEADERBOARD = [
  { rank: 1, name: 'Aizat K.', xp: 1840, badge: '🧙', level: 19 },
  { rank: 2, name: 'Bekzod M.', xp: 1620, badge: '🏆', level: 17 },
  { rank: 3, name: 'Dana S.', xp: 1455, badge: '⭐', level: 15 },
  { rank: 4, name: 'Elnur T.', xp: 1200, badge: '🎯', level: 13 },
  { rank: 5, name: 'Farida U.', xp: 980, badge: '📚', level: 10 },
  { rank: 6, name: 'Gulnara R.', xp: 840, badge: '🌱', level: 9 },
  { rank: 7, name: 'Hamza A.', xp: 720, badge: '⚡', level: 8 },
  { rank: 8, name: 'Iroda B.', xp: 610, badge: '🐸', level: 7 },
];

export const FLEXBOX_LEVELS = [
  {
    id: 1,
    instruction: 'Move the frog to the right lily pad!',
    hint: 'Use justify-content to position items horizontally',
    frogs: [{ emoji: '🐸', position: 'left' }],
    target: 'flex-end',
    property: 'justify-content',
    options: ['flex-start', 'center', 'flex-end', 'space-between'],
    correct: 'flex-end',
  },
  {
    id: 2,
    instruction: 'Center the frog on the lily pad!',
    hint: 'Center means exactly in the middle',
    frogs: [{ emoji: '🐸', position: 'left' }],
    target: 'center',
    property: 'justify-content',
    options: ['flex-start', 'center', 'flex-end', 'space-around'],
    correct: 'center',
  },
  {
    id: 3,
    instruction: 'Spread the frogs across all lily pads!',
    hint: 'space-between puts equal space between items',
    frogs: [{ emoji: '🐸' }, { emoji: '🐸' }, { emoji: '🐸' }],
    target: 'spread',
    property: 'justify-content',
    options: ['center', 'space-around', 'space-between', 'flex-end'],
    correct: 'space-between',
  },
  {
    id: 4,
    instruction: 'Move the frog to the bottom!',
    hint: 'align-items controls the cross-axis (vertical)',
    frogs: [{ emoji: '🐸' }],
    target: 'bottom',
    property: 'align-items',
    options: ['flex-start', 'center', 'flex-end', 'stretch'],
    correct: 'flex-end',
  },
  {
    id: 5,
    instruction: 'Center the frog both ways!',
    hint: 'You need both justify-content and align-items',
    frogs: [{ emoji: '🐸' }],
    target: 'center-both',
    property: 'both',
    options: ['flex-start', 'center', 'flex-end', 'space-around'],
    correct: 'center',
  },
];

export const TYPING_SNIPPETS = [
  { id: 1, code: `const sum = (a, b) => a + b;`, difficulty: 'easy' },
  { id: 2, code: `console.log("Hello, World!");`, difficulty: 'easy' },
  { id: 3, code: `const arr = [1, 2, 3].map(x => x * 2);`, difficulty: 'medium' },
  { id: 4, code: `document.querySelector('.btn').addEventListener('click', () => {});`, difficulty: 'medium' },
  { id: 5, code: `const fetch = async (url) => { const res = await get(url); return res.json(); };`, difficulty: 'hard' },
];
