part of 'signup_cubit.dart';

class SignupState {
  final bool obscurePassword;
  final bool obscureConfirm;

  const SignupState({
    this.obscurePassword = true,
    this.obscureConfirm = true,
  });

  SignupState copyWith({bool? obscurePassword, bool? obscureConfirm}) {
    return SignupState(
      obscurePassword: obscurePassword ?? this.obscurePassword,
      obscureConfirm: obscureConfirm ?? this.obscureConfirm,
    );
  }
}



