import 'package:aura/app/theme/text_style/app_text_style.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../routes/names.dart';
import '../../../widgets/custom_textform_lables.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  bool _obscurePassword = true;
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();

  // Read role passed from SelectRoleScreen
  late final Map<String, dynamic> _role =
      (Get.arguments as Map<String, dynamic>?) ??
      {'id': '1', 'title': 'ADMINISTRATOR', 'level': 'LEVEL: EXECUTIVE'};

  String get _roleTitle => _role['title'] as String? ?? 'ADMINISTRATOR';

  String _destinationRoute() {
    switch (_role['id']) {
      case '2':
        return PageRoutes.receptioninstMainScreen;
      case '3':
        return PageRoutes.therapistDashboard;
      default:
        return PageRoutes.adminMainScreen;
    }
  }

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
                      /// LOGO + ROLE
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
                              '${_roleTitle[0]}${_roleTitle.substring(1).toLowerCase()} Portal',
                              style: AppTextStyles.headingMedium,
                            ),
                            const SizedBox(height: 12),
                          ],
                        ),
                      ),

                      const SizedBox(height: 50),

                      CustomLabel(text: 'EMAIL'),
                      CustomTextField(
                        controller: _emailController,
                        hint: 'clinician@aura.com',
                        keyboardType: TextInputType.emailAddress,
                      ),

                      const SizedBox(height: 28),

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
                          onPressed: () => setState(
                            () => _obscurePassword = !_obscurePassword,
                          ),
                        ),
                      ),

                      const SizedBox(height: 32),

                      PrimaryButton(
                        label: 'LOGIN',
                        onTap: () => Get.offAllNamed(_destinationRoute()),
                      ),

                      const SizedBox(height: 24),

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

                      // No sign-up link — removed as requested
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

  String _accessLabel(String level, String title) {
    if (level.contains('EXECUTIVE')) return 'Administrator Portal';
    if (level.contains('OPERATIONS')) return 'Receptionist Portal';
    return 'Therapist Portal';
  }
}
