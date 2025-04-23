declare module 'react' {
  export type ReactNode = 
    | string
    | number
    | boolean
    | null
    | undefined
    | JSX.Element
    | Array<ReactNode>;

  export interface ChangeEvent<T> {
    target: T;
    currentTarget: T;
    preventDefault(): void;
    stopPropagation(): void;
  }

  export interface FormEvent {
    preventDefault(): void;
    stopPropagation(): void;
  }

  export function useState<T>(initialState: T | (() => T)): [T, (newState: T | ((prevState: T) => T)) => void];
  export function useEffect(effect: () => void | (() => void), deps?: readonly any[]): void;
  export function useCallback<T extends (...args: any[]) => any>(callback: T, deps: readonly any[]): T;
  export function useMemo<T>(factory: () => T, deps: readonly any[]): T;
  export function useRef<T>(initialValue: T): { current: T };
  export function useContext<T>(context: React.Context<T>): T;

  export interface Context<T> {
    Provider: Provider<T>;
    Consumer: Consumer<T>;
  }
  
  export interface Provider<T> {
    (props: { value: T; children: ReactNode }): JSX.Element;
  }
  
  export interface Consumer<T> {
    (props: { children: (value: T) => ReactNode }): JSX.Element;
  }
  
  export function createContext<T>(defaultValue: T): Context<T>;

  export type FC<P = {}> = (props: P) => JSX.Element | null;
  
  export function jsx(type: any, props: any): JSX.Element;
  export function jsxs(type: any, props: any): JSX.Element;
} 