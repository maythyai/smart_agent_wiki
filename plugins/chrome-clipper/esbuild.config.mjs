import esbuild from 'esbuild';

const isWatch = process.argv.includes('--watch');

const buildConfig = {
  // Service worker (background) - IIFE format for MV3
  background: {
    entryPoints: ['src/background/index.ts'],
    outfile: 'dist/background.js',
    format: 'iife',
    bundle: true,
    minify: !isWatch,
    sourcemap: isWatch ? 'inline' : false,
    target: ['es2022'],
    platform: 'browser',
    external: [],
  },
  // Content script - IIFE format
  content: {
    entryPoints: ['src/content/index.ts'],
    outfile: 'dist/content.js',
    format: 'iife',
    bundle: true,
    minify: !isWatch,
    sourcemap: isWatch ? 'inline' : false,
    target: ['es2022'],
    platform: 'browser',
  },
  // Popup script - ESM format for module script tag
  popup: {
    entryPoints: ['src/popup/index.ts'],
    outfile: 'dist/popup.js',
    format: 'esm',
    bundle: true,
    minify: !isWatch,
    sourcemap: isWatch ? 'inline' : false,
    target: ['es2022'],
    platform: 'browser',
  },
  // Offscreen document - ESM format
  offscreen: {
    entryPoints: ['src/offscreen/offscreen.ts'],
    outfile: 'dist/offscreen.js',
    format: 'esm',
    bundle: true,
    minify: !isWatch,
    sourcemap: isWatch ? 'inline' : false,
    target: ['es2022'],
    platform: 'browser',
  },
};

async function build() {
  try {
    // Build all entry points
    await Promise.all([
      esbuild.build(buildConfig.background),
      esbuild.build(buildConfig.content),
      esbuild.build(buildConfig.popup),
      esbuild.build(buildConfig.offscreen),
    ]);

    console.log('Build complete!');
  } catch (error) {
    console.error('Build failed:', error);
    process.exit(1);
  }
}

if (isWatch) {
  // Watch mode - rebuild on changes
  Promise.all([
    esbuild.context(buildConfig.background).then(ctx => ctx.watch()),
    esbuild.context(buildConfig.content).then(ctx => ctx.watch()),
    esbuild.context(buildConfig.popup).then(ctx => ctx.watch()),
    esbuild.context(buildConfig.offscreen).then(ctx => ctx.watch()),
  ]).then(() => {
    console.log('Watching for changes...');
  });
} else {
  build();
}