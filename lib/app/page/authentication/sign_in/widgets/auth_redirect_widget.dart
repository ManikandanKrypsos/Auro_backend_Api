import 'package:flutter/material.dart';

class AuthRedirectText extends StatelessWidget {
  final String normalText;
  final String actionText;
  final VoidCallback onTap;

  const AuthRedirectText({
    super.key,
    required this.normalText,
    required this.actionText,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(
            normalText,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: Colors.white.withOpacity(0.5),
              fontSize: 13,
            ),
          ),
          GestureDetector(
            onTap: onTap,
            child: Text(
              actionText,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: Color(0xFFC6A769), // or ColorResources.primaryColor
                fontSize: 13,
                fontWeight: FontWeight.w600,
              ),
            ),
          ),
        ],
      ),
    );
  }
}