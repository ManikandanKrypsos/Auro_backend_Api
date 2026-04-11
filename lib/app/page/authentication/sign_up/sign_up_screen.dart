import 'package:aura/app/theme/text_style/app_text_style.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';

import '../../../routes/names.dart';
import '../../../widgets/custom_textform_lables.dart';
import '../sign_in/widgets/auth_redirect_widget.dart';
import 'cubit/signup_cubit.dart';

class SignupScreen extends StatelessWidget {
  const SignupScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => SignupCubit(),
      child: const _SignupView(),
    );
  }
}

class _SignupView extends StatelessWidget {
  const _SignupView();

  @override
  Widget build(BuildContext context) {
    final cubit = context.read<SignupCubit>();

    return Scaffold(
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Center(
                child: Text(
                  'Create Account',
                  textAlign: TextAlign.center,
                  style: AppTextStyles.headingLarge
                ),
              ),

              const SizedBox(height: 12),

              Center(
                child: Text(
                  'Experience the pinnacle of aesthetic excellence',
                  textAlign: TextAlign.center,
                    style: AppTextStyles.headingMedium
                ),
              ),

              const SizedBox(height: 40),

              CustomLabel(text: 'FULL NAME'),
              CustomTextField(
                controller: cubit.nameController,
                hint: 'Alexander Sterling',
              ),

              const SizedBox(height: 28),

              CustomLabel(text: 'EMAIL ADDRESS'),
              CustomTextField(
                controller: cubit.emailController,
                hint: 'alexander@luxuryclinic.com',
                keyboardType: TextInputType.emailAddress,
              ),

              const SizedBox(height: 28),

              CustomLabel(text: 'PHONE NUMBER'),
              CustomTextField(
                controller: cubit.phoneController,
                hint: '+1 (555) 000-0000',
                keyboardType: TextInputType.phone,
              ),

              const SizedBox(height: 28),

              CustomLabel(text: 'PASSWORD'),
              BlocBuilder<SignupCubit, SignupState>(
                buildWhen: (prev, curr) =>
                    prev.obscurePassword != curr.obscurePassword,
                builder: (context, state) => CustomTextField(
                  controller: cubit.passwordController,
                  hint: '••••••••••••',
                  obscure: state.obscurePassword,
                  suffix: IconButton(
                    icon: Icon(
                      state.obscurePassword
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: Colors.white38,
                      size: 20,
                    ),
                    onPressed: cubit.togglePasswordVisibility,
                  ),
                ),
              ),

              const SizedBox(height: 28),

              CustomLabel(text: 'CONFIRM PASSWORD'),
              BlocBuilder<SignupCubit, SignupState>(
                buildWhen: (prev, curr) =>
                    prev.obscureConfirm != curr.obscureConfirm,
                builder: (context, state) => CustomTextField(
                  controller: cubit.confirmController,
                  hint: '••••••••••••',
                  obscure: state.obscureConfirm,
                  suffix: IconButton(
                    icon: Icon(
                      state.obscureConfirm
                          ? Icons.visibility_off_outlined
                          : Icons.visibility_outlined,
                      color: Colors.white38,
                      size: 20,
                    ),
                    onPressed: cubit.toggleConfirmVisibility,
                  ),
                ),
              ),

              const SizedBox(height: 32),

              PrimaryButton(label: 'CREATE ACCOUNT', onTap: () {       Get.offAllNamed(PageRoutes.adminMainScreen);}),

              const SizedBox(height: 24),

              AuthRedirectText(
                normalText: "Already have a professional account? ",
                actionText: "Log in here",
                onTap: () => Get.offNamed(PageRoutes.signInScreen),
              ),

              const SizedBox(height: 40),
            ],
          ),
        ),
      ),
    );
  }
}