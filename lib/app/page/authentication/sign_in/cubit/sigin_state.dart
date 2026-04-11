part of 'sigin_cubit.dart';

class LoginState {
  final bool obscurePassword;

  const LoginState({this.obscurePassword = true});

  LoginState copyWith({bool? obscurePassword}) {
    return LoginState(obscurePassword: obscurePassword ?? this.obscurePassword);
  }
}
