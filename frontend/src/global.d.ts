// src/global.d.ts

// CSS モジュール用
declare module '*.module.css' {
    const classes: { [key: string]: string };
    export default classes;
  }
  
  // グローバル CSS 用 
  declare module '*.css';
  