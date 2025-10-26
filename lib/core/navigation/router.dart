import 'package:go_router/go_router.dart';
import 'package:firebase_auth/firebase_auth.dart';

import '../../screens/login_screen.dart';
import '../../screens/register_screen.dart';
import '../../screens/home_screen.dart';

final router = GoRouter(
  initialLocation: '/',
  redirect: (context, state) {
    final user = FirebaseAuth.instance.currentUser;

    if (user == null && state.uri.toString() != '/register') {
      return '/login';
    }
    if (user != null &&
        (state.uri.toString() == '/login' || state.uri.toString() == '/register')) {
      return '/';
    }
    return null;
  },
  routes: [
    GoRoute(path: '/', builder: (context, state) => const HomeScreen()),
    GoRoute(path: '/login', builder: (context, state) => const LoginScreen()),
    GoRoute(path: '/register', builder: (context, state) => const RegisterScreen()),

  ],
);

