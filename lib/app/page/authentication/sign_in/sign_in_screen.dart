import 'package:aura/app/theme/text_style/app_text_style.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../routes/names.dart';
import '../../../widgets/custom_textform_lables.dart';
import 'widgets/auth_redirect_widget.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _obscurePassword = true;

  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: SafeArea(
        child: LayoutBuilder(
          builder: (context, constraints) {
            return SingleChildScrollView(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: ConstrainedBox(
                constraints: BoxConstraints(minHeight: constraints.maxHeight),
                child: Center(
                  child: Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      /// LOGO
                      Center(
                        child: Column(
                          children: [
                            const Text(
                              'A U R A',
                              style: TextStyle(
                                fontFamily: 'CormorantGaramond',
                                color: Colors.white,
                                fontSize: 40,
                                fontWeight: FontWeight.w300,
                                letterSpacing: 4,
                              ),
                            ),
                            Text(
                              'Aesthetic Excellence',
                              style: AppTextStyles.headingMedium
                            ),
                          ],
                        ),
                      ),

                      const SizedBox(height: 50),

                      /// EMAIL
                      CustomLabel(text: 'EMAIL'),
                      CustomTextField(
                        controller: _emailController,
                        hint: 'clinician@aura.com',
                        keyboardType: TextInputType.emailAddress,
                      ),

                      const SizedBox(height: 28),

                      /// PASSWORD
                      CustomLabel(text: 'PASSWORD'),
                      CustomTextField(
                        controller: _passwordController,
                        hint: '••••••••',
                        obscure: _obscurePassword,
                        suffix: IconButton(
                          icon: Icon(
                            _obscurePassword
                                ? Icons.visibility_outlined
                                : Icons.visibility_off_outlined,
                            color: Colors.white38,
                            size: 20,
                          ),
                          onPressed: () {
                            setState(() {
                              _obscurePassword = !_obscurePassword;
                            });
                          },
                        ),
                      ),

                      const SizedBox(height: 32),

                      /// LOGIN BUTTON
                      PrimaryButton(label: 'LOGIN TO DASHBOARD', onTap: () {
                          Get.offAllNamed(PageRoutes.adminMainScreen);
                      }),

                      const SizedBox(height: 24),

                      /// FORGOT PASSWORD
                      Center(
                        child: GestureDetector(
                          onTap: () {},
                          child: Text(
                            'Forgot Password?',
                            style: TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: Colors.white.withOpacity(0.55),
                              fontSize: 15,
                              fontStyle: FontStyle.italic,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ),
                      ),

                      const SizedBox(height: 24),

                      AuthRedirectText(
                        normalText: "Create your professional account ",
                        actionText: "Sign up here",
                        onTap: () => Get.offNamed(PageRoutes.signupScreen),
                      ),
                      const SizedBox(height: 40),
                    ],
                  ),
                ),
              ),
            );
          },
        ),
      ),
    );
  }
}
