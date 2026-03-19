import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';

import '../../../../theme/color/color.dart';
import '../../../authentication/sign_up/sign_up_screen.dart';
import '../../cubit/role_cubit.dart';

class RoleCard extends StatelessWidget {
  final Map<String, dynamic> role;
  final String selectedRole;
  final Function(String) onSelect;

  const RoleCard({
    super.key,
    required this.role,
    required this.selectedRole,
    required this.onSelect,
  });

  @override
  Widget build(BuildContext context) {
    final isSelected = selectedRole == role['id'];

    return GestureDetector(
      onTap: () => onSelect(role['id']),
      child: Container(
        margin: const EdgeInsets.only(bottom: 20),
        decoration: BoxDecoration(
          color: ColorResources.blackColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: isSelected
                ? ColorResources.primaryColor
                : Colors.transparent,
            width: 1.5,
          ),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            /// Image
            Stack(
              children: [
                ClipRRect(
                  borderRadius:
                      const BorderRadius.vertical(top: Radius.circular(16)),
                  child: Image.asset(
                    role['image'],
                    height: 180,
                    width: double.infinity,
                    fit: BoxFit.cover,
                    errorBuilder: (_, __, ___) => Container(
                      height: 180,
                      color: const Color(0xFF2A2A2A),
                      child: const Center(
                        child: Icon(Icons.image,
                            color: Colors.white24, size: 48),
                      ),
                    ),
                  ),
                ),
              ],
            ),

            /// Content
            Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  /// Level
                  Text(
                    role['level'],
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.5,
                    ),
                  ),

                  const SizedBox(height: 6),

                  /// Title
                  Text(
                    role['title'],
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: Colors.white,
                      fontSize: 28,
                      fontWeight: FontWeight.w300,
                      letterSpacing: 4.0,
                    ),
                  ),

                  const SizedBox(height: 8),

                  /// Description
                  Text(
                    role['description'],
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: Colors.white.withOpacity(0.65),
                      fontSize: 14,
                      height: 1.6,
                    ),
                  ),

                  const SizedBox(height: 16),

                  /// Button
                  SizedBox(
                    width: double.infinity,
                    child: OutlinedButton(
                      onPressed: () {
                     context.read<RoleCubit>().selectRole(role['id']);
                        
                         Get.to(() => SignupScreen());
                      },
                      style: OutlinedButton.styleFrom(
                        side: BorderSide(
                          color: isSelected
                              ? ColorResources.primaryColor
                              : Colors.white38,
                        ),
                        backgroundColor: isSelected
                            ? ColorResources.primaryColor.withOpacity(0.15)
                            : Colors.transparent,
                        padding:
                            const EdgeInsets.symmetric(vertical: 14),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(30),
                        ),
                      ),
                      child: Text(
                        role['buttonText'],
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: isSelected
                              ? ColorResources.primaryColor
                              : Colors.white,
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 2.5,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}