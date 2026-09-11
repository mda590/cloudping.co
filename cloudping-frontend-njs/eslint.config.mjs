// Flat config. `next lint` was removed in Next.js 16, so ESLint runs directly
// via the `lint` script and eslint-config-next is imported as flat config
// rather than through the @eslint/eslintrc compatibility shim.
import nextCoreWebVitals from "eslint-config-next/core-web-vitals";
import nextTypeScript from "eslint-config-next/typescript";

const eslintConfig = [
  ...nextCoreWebVitals,
  ...nextTypeScript,
  {
    // `next lint` used to apply these implicitly.
    ignores: [".next/**", "next-env.d.ts", "node_modules/**"],
  },
];

export default eslintConfig;
