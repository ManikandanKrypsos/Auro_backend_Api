import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
part 'sigin_state.dart';

class LoginCubit extends Cubit<LoginState> {
  LoginCubit() : super(const LoginState());

  final emailController = TextEditingController();
  final passwordController = TextEditingController();

  void togglePasswordVisibility() =>
      emit(state.copyWith(obscurePassword: !state.obscurePassword));

  @override
  Future<void> close() async {
    emailController.dispose();
    passwordController.dispose();
    await super.close();
  }
}
