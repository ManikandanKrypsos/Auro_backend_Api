import 'package:flutter/material.dart';
import '../theme/color/color.dart';

class CustomTextField extends StatelessWidget {
  final TextEditingController controller;
  final String hint;
  final bool obscure;
  final TextInputType keyboardType;
  final Widget? suffix;
  final int? maxLine;

  const CustomTextField({
    super.key,
    required this.controller,
    required this.hint,
    this.obscure = false,
    this.keyboardType = TextInputType.text,
    this.suffix,
    this.maxLine = 1,
  });

  @override
  Widget build(BuildContext context) {
    return TextField(
      controller: controller,
      maxLines: obscure ? 1 : maxLine,
      obscureText: obscure,
      keyboardType: keyboardType,
      style: const TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.whiteColor,
        fontSize: 15,
      ),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: ColorResources.whiteColor.withOpacity(0.25),
          fontSize: 15,
          fontStyle: FontStyle.italic,
        ),
        filled: true,
        fillColor: ColorResources.cardColor,
        contentPadding:
            const EdgeInsets.symmetric(horizontal: 14, vertical: 13),

        /// ADD THIS
        suffixIcon: suffix,

        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:
              const BorderSide(color: ColorResources.borderColor, width: 0.5),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:
              const BorderSide(color: ColorResources.borderColor, width: 0.5),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide:
              const BorderSide(color: ColorResources.primaryColor, width: 0.8),
        ),
      ),
      cursorColor: ColorResources.primaryColor,
    );
  }
}