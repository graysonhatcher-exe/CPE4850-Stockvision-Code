// ignore_for_file: type=lint

import 'package:firebase_core/firebase_core.dart' show FirebaseOptions;
import 'package:flutter/foundation.dart'
    show defaultTargetPlatform, kIsWeb, TargetPlatform;

class DefaultFirebaseOptions {
  static FirebaseOptions get currentPlatform {
    if (kIsWeb) {
      return web;
    }
    switch (defaultTargetPlatform) {
      case TargetPlatform.android:
        return android;
      case TargetPlatform.iOS:
        return ios;
      case TargetPlatform.macOS:
        return macos;
      case TargetPlatform.windows:
        return windows;
      case TargetPlatform.linux:
        throw UnsupportedError(
          'DefaultFirebaseOptions have not been configured for Linux.',
        );
      default:
        throw UnsupportedError(
          'DefaultFirebaseOptions are not supported for this platform.',
        );
    }
  }

  static const FirebaseOptions web = FirebaseOptions(
    apiKey: 'AIzaSyCDIPJ4_-Q1Vfwd_snzNmDjx0RIYfxBPyM',
    appId: '1:425301891972:web:3478574713070187ea9bd1',
    messagingSenderId: '425301891972',
    projectId: 'test-d1cec',
    authDomain: 'test-d1cec.firebaseapp.com',
    databaseURL: 'https://test-d1cec-default-rtdb.firebaseio.com',
    storageBucket: 'test-d1cec.appspot.com',
    measurementId: 'G-QCQL5LL316',
  );

  static const FirebaseOptions android = FirebaseOptions(
    apiKey: 'AIzaSyCN5QK_qnF7oy9FB-IhwlbZz4PSIQMuJYM',
    appId: '1:425301891972:android:1806ea41a8f280dcea9bd1',
    messagingSenderId: '425301891972',
    projectId: 'test-d1cec',
    databaseURL: 'https://test-d1cec-default-rtdb.firebaseio.com',
    storageBucket: 'test-d1cec.appspot.com',
  );

  static const FirebaseOptions ios = FirebaseOptions(
    apiKey: 'AIzaSyDs6alLQKJ6pgqB_IgMOYVdby5EShb88vc',
    appId: '1:425301891972:ios:6a09f92a7dbc509aea9bd1',
    messagingSenderId: '425301891972',
    projectId: 'test-d1cec',
    databaseURL: 'https://test-d1cec-default-rtdb.firebaseio.com',
    storageBucket: 'test-d1cec.appspot.com',
    iosBundleId: 'com.example.myPantryApp',
  );

  static const FirebaseOptions macos = FirebaseOptions(
    apiKey: 'AIzaSyDs6alLQKJ6pgqB_IgMOYVdby5EShb88vc',
    appId: '1:425301891972:ios:6a09f92a7dbc509aea9bd1',
    messagingSenderId: '425301891972',
    projectId: 'test-d1cec',
    databaseURL: 'https://test-d1cec-default-rtdb.firebaseio.com',
    storageBucket: 'test-d1cec.appspot.com',
    iosBundleId: 'com.example.myPantryApp',
  );

  static const FirebaseOptions windows = FirebaseOptions(
    apiKey: 'AIzaSyCDIPJ4_-Q1Vfwd_snzNmDjx0RIYfxBPyM',
    appId: '1:425301891972:web:f31aef4b473c6afeea9bd1',
    messagingSenderId: '425301891972',
    projectId: 'test-d1cec',
    authDomain: 'test-d1cec.firebaseapp.com',
    databaseURL: 'https://test-d1cec-default-rtdb.firebaseio.com',
    storageBucket: 'test-d1cec.appspot.com',
    measurementId: 'G-2YDXSLY803',
  );
}
