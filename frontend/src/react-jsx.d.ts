// React JSX Runtime型定義
/// <reference types="react" />
/// <reference types="react/jsx-runtime" />

declare module 'react/jsx-runtime' {
  export { jsx, jsxs } from 'react';
}

declare module 'react/jsx-dev-runtime' {
  export { jsx, jsxs } from 'react';
}

// React名前空間の型定義
declare namespace React {
  interface HTMLAttributes<T> {
    className?: string;
    style?: React.CSSProperties;
    [key: string]: any;
  }
  
  interface CSSProperties {
    [key: string]: string | number | undefined;
  }
  
  interface ButtonHTMLAttributes<T> extends HTMLAttributes<T> {
    type?: 'button' | 'submit' | 'reset';
    disabled?: boolean;
    onClick?: (event: any) => void;
  }
  
  interface InputHTMLAttributes<T> extends HTMLAttributes<T> {
    type?: string;
    value?: string | number | readonly string[];
    onChange?: (event: ChangeEvent<HTMLInputElement>) => void;
    accept?: string;
    placeholder?: string;
    required?: boolean;
  }
  
  interface TextareaHTMLAttributes<T> extends HTMLAttributes<T> {
    value?: string | number | readonly string[];
    onChange?: (event: ChangeEvent<HTMLTextAreaElement>) => void;
    rows?: number;
    placeholder?: string;
    required?: boolean;
  }
  
  interface SelectHTMLAttributes<T> extends HTMLAttributes<T> {
    value?: string | number | readonly string[];
    onChange?: (event: ChangeEvent<HTMLSelectElement>) => void;
  }
  
  interface DetailedHTMLProps<P extends HTMLAttributes<T>, T> {
    [key: string]: any;
  }
  
  interface FormHTMLAttributes<T> extends HTMLAttributes<T> {
    onSubmit?: (event: FormEvent) => void;
  }
  
  interface LabelHTMLAttributes<T> extends HTMLAttributes<T> {}
  
  interface FormEvent {
    preventDefault(): void;
  }
  
  interface ChangeEvent<T> {
    target: T;
  }
  
  interface FC<P = {}> {
    (props: P): JSX.Element | null;
  }
}

// JSX要素の型定義
declare namespace JSX {
  interface IntrinsicElements {
    div: React.DetailedHTMLProps<React.HTMLAttributes<HTMLDivElement>, HTMLDivElement>;
    span: React.DetailedHTMLProps<React.HTMLAttributes<HTMLSpanElement>, HTMLSpanElement>;
    h1: React.DetailedHTMLProps<React.HTMLAttributes<HTMLHeadingElement>, HTMLHeadingElement>;
    p: React.DetailedHTMLProps<React.HTMLAttributes<HTMLParagraphElement>, HTMLParagraphElement>;
    button: React.DetailedHTMLProps<React.ButtonHTMLAttributes<HTMLButtonElement>, HTMLButtonElement>;
    input: React.DetailedHTMLProps<React.InputHTMLAttributes<HTMLInputElement>, HTMLInputElement>;
    textarea: React.DetailedHTMLProps<React.TextareaHTMLAttributes<HTMLTextAreaElement>, HTMLTextAreaElement>;
    form: React.DetailedHTMLProps<React.FormHTMLAttributes<HTMLFormElement>, HTMLFormElement>;
    label: React.DetailedHTMLProps<React.LabelHTMLAttributes<HTMLLabelElement>, HTMLLabelElement>;
    select: React.DetailedHTMLProps<React.SelectHTMLAttributes<HTMLSelectElement>, HTMLSelectElement>;
    option: React.DetailedHTMLProps<React.HTMLAttributes<HTMLOptionElement>, HTMLOptionElement>;
    [elemName: string]: any;
  }
} 