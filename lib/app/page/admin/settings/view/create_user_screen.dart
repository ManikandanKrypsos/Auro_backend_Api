import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/custom_appbar.dart';
import '../../../../widgets/custom_textform_lables.dart';
import '../../../../widgets/custom_textformfeild.dart';
import '../../../../widgets/primary_button.dart';

class CreateUserScreen extends StatefulWidget {
  const CreateUserScreen({super.key});

  @override
  State<CreateUserScreen> createState() => _CreateUserScreenState();
}

class _CreateUserScreenState extends State<CreateUserScreen> {
  bool _obscurePassword = true;
  String _selectedRole = 'Receptionist';
  String _selectedStatus = 'Active';


  final TextEditingController _emailController = TextEditingController();
  final TextEditingController _phoneController = TextEditingController();
  final TextEditingController _usernameController = TextEditingController();
  final TextEditingController _passwordController = TextEditingController();
  final TextEditingController _confirmPasswordController = TextEditingController();
  final List<String> _roles = ['Admin', 'Receptionist', 'Therapist'];
  final List<String> _statuses = ['Active', 'Inactive'];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'CREATE USER'),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'ACCOUNT DETAILS',
                style: AppTextStyles.headingSmall.copyWith(
                  fontSize: 11,
                  color: ColorResources.liteTextColor,
                  letterSpacing: 3.5,
                ),
              ),
              const SizedBox(height: 20),

         
             CustomLabel(text: 'USERNAME'),
              CustomTextField(
                controller: _usernameController,
                hint: 'e.g. sarahj',
              ),
              const SizedBox(height: 20),

              CustomLabel(text: 'EMAIL ADDRESS'),
              CustomTextField(
                controller: _emailController,
                hint: 'e.g. sarah@aura.com',
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 20),

              CustomLabel(text: 'PHONE NUMBER'),
              CustomTextField(
                controller: _phoneController,
                hint: '+1 (555) 000-0000',
                keyboardType: TextInputType.phone,
              ),
              const SizedBox(height: 20),


              CustomLabel(text: 'PASSWORD'),
              CustomTextField(
                controller: _passwordController,
                hint: '••••••••••••',
                obscure: _obscurePassword,
                suffix: IconButton(
                  icon: Icon(
                    _obscurePassword
                        ? Icons.visibility_off_outlined
                        : Icons.visibility_outlined,
                    color: ColorResources.liteTextColor,
                    size: 20,
                  ),
                  onPressed: () {
                    setState(() {
                      _obscurePassword = !_obscurePassword;
                    });
                  },
                ),
              ),
              const SizedBox(height: 20),


              CustomLabel(text: 'CONFIRM PASSWORD'),
              CustomTextField(
                controller: _confirmPasswordController,
                hint: '••••••••••••',
                obscure: _obscurePassword,
                suffix: IconButton(
                  icon: Icon(
                    _obscurePassword
                        ? Icons.visibility_off_outlined
                        : Icons.visibility_outlined,
                    color: ColorResources.liteTextColor,
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

              Text(
                'ACCESS & PERMISSIONS',
                style: AppTextStyles.headingSmall.copyWith(
                  fontSize: 11,
                  color: ColorResources.liteTextColor,
                  letterSpacing: 3.5,
                ),
              ),
              const SizedBox(height: 20),

              CustomLabel(text: 'ROLE'),
              _buildDropdown(
                value: _selectedRole,
                items: _roles,
                onChanged: (val) {
                  if (val != null) setState(() => _selectedRole = val);
                },
              ),
              const SizedBox(height: 20),

              CustomLabel(text: 'STATUS'),
              _buildDropdown(
                value: _selectedStatus,
                items: _statuses,
                onChanged: (val) {
                  if (val != null) setState(() => _selectedStatus = val);
                },
              ),
              const SizedBox(height: 48),

              PrimaryButton(
                label: 'CREATE USER',
                onTap: () {
                  Get.back();
                  Get.snackbar(
                    'Success',
                    'User created successfully',
                    snackPosition: SnackPosition.BOTTOM,
                    backgroundColor: ColorResources.primaryColor.withOpacity(0.2),
                    colorText: ColorResources.primaryColor,
                  );
                },
              ),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildDropdown({
    required String value,
    required List<String> items,
    required void Function(String?) onChanged,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(
          color: ColorResources.primaryColor.withOpacity(0.25),
          width: 0.5,
        ),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<String>(
          value: value,
          isExpanded: true,
          dropdownColor: ColorResources.cardColor,
          icon: const Icon(Icons.keyboard_arrow_down,
              color: ColorResources.liteTextColor),
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 16,
            fontWeight: FontWeight.w400,
          ),
          items: items.map((String item) {
            return DropdownMenuItem<String>(
              value: item,
              child: Text(item),
            );
          }).toList(),
          onChanged: onChanged,
        ),
      ),
    );
  }
}
