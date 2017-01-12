var gulp = require('gulp');

var clean = require('gulp-clean');

var browserSync = require('browser-sync');

var sass = require('gulp-sass');
var postcss = require('gulp-postcss');
var sourcemaps = require('gulp-sourcemaps');
var autoprefixer = require('autoprefixer');
var cssnano = require('cssnano');


// var svgstore = require('gulp-svgstore');
// var path = require('path');
// var inject = require('gulp-inject');
// var svgmin = require('gulp-svgmin');




// Browsersync
// -------------------------------------
gulp.task('browser-sync', function() {
  browserSync({
    server : {},
    ghostMode: false
  });
});




// Clean
// -------------------------------------
gulp.task('clean', function(){
  return gulp.src(['dist/css/*.css'])
  .pipe(clean());
});




// SVG + Inline
// -------------------------------------
// gulp.task('svg', function() {
//   var svgs = gulp.src('static/icons/*.svg')
//   .pipe(svgmin(function(file) {
//     var prefix = path.basename(file.relative, path.extname(file.relative));
//     return {
//       plugins: [{
//         cleanupIDs: {
//           prefix: prefix + '-',
//           minify: true
//         }
//       }]
//     }
//   }))
//   .pipe(svgstore( { inlineSvg: true }))
//   .pipe(gulp.dest('static/icons'))

//   function fileContents(filePath, file) {
//     return file.contents.toString();
//   }

//   return gulp.src('index.html')
//   .pipe(inject(svgs, { transform: fileContents } ))
//   .pipe(gulp.dest(''));
// });




// Sass
// -------------------------------------
gulp.task('sass', function(){
  var processors = [
    autoprefixer( {browsers: ['last 2 versions']} ),
    cssnano
  ];

 return gulp.src(['source/scss/**/*.scss'])
 .pipe(sourcemaps.init())
 .pipe( sass().on('error', sass.logError) )
 .pipe(sourcemaps.init())
 .pipe(postcss(processors))
 .pipe(sourcemaps.write('./'))
 .pipe(gulp.dest('dist/css'))
 .pipe(browserSync.stream());
});




// // Watch
// // -------------------------------------
gulp.task('watch', function(){
  gulp.watch('source/scss/**/*.scss', ['sass']);
});




// // Default
// // -------------------------------------
gulp.task('default', ['sass', 'watch', 'browser-sync']);