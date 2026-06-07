import { createContext, useCallback, useContext, useMemo, useState } from "react";

interface NavLayoutContextValue {
  collapsed: boolean;
  toggleCollapsed: () => void;
  navWidth: number;
}

const NavLayoutContext = createContext<NavLayoutContextValue | null>(null);

type ProviderProps = {
  children: React.ReactNode;
  expandedWidth: number;
  collapsedWidth: number;
};

export function NavLayoutProvider({
  children,
  expandedWidth,
  collapsedWidth,
}: ProviderProps) {
  const [collapsed, setCollapsed] = useState(false);

  const toggleCollapsed = useCallback(() => {
    setCollapsed((prev) => !prev);
  }, []);

  const value = useMemo(
    () => ({
      collapsed,
      toggleCollapsed,
      navWidth: collapsed ? collapsedWidth : expandedWidth,
    }),
    [collapsed, collapsedWidth, expandedWidth, toggleCollapsed],
  );

  return (
    <NavLayoutContext.Provider value={value}>{children}</NavLayoutContext.Provider>
  );
}

export function useNavLayout() {
  const context = useContext(NavLayoutContext);
  if (!context) {
    throw new Error("useNavLayout must be used within NavLayoutProvider");
  }
  return context;
}
