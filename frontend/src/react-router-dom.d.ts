declare module 'react-router-dom' {
  export function useNavigate(): (path: string, options?: { replace?: boolean; state?: any }) => void;
  export function useParams<T extends Record<string, string | undefined>>(): T;
  export function useLocation(): { pathname: string; search: string; hash: string; state: any };
  export function Link(props: { to: string; className?: string; children?: React.ReactNode }): JSX.Element;
  export function NavLink(props: { to: string; className?: string; children?: React.ReactNode }): JSX.Element;
  export function Outlet(): JSX.Element;
  export function Routes(props: { children: React.ReactNode }): JSX.Element;
  export function Route(props: { path: string; element: React.ReactNode }): JSX.Element;
  export function BrowserRouter(props: { children: React.ReactNode }): JSX.Element;
  export function Navigate(props: { to: string; replace?: boolean; state?: any }): JSX.Element;
  
  // 一般的なHistory APIタイプ
  export interface Location {
    pathname: string;
    search: string;
    hash: string;
    state: any;
    key?: string;
  }
  
  // アプリケーション固有のタイプ
  export interface LocationState {
    from?: string;
  }
} 