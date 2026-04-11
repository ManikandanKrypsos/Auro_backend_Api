import 'package:aura/app/routes/names.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:get/get.dart';
import '../../../resources/asset_resources.dart';
import '../../../theme/color/color.dart';
import '../cubit/role_cubit.dart';

class SelectRoleScreen extends StatelessWidget {
  const SelectRoleScreen({super.key});

  final List<Map<String, dynamic>> roles = const [
    {
      'id': '1',
      'level': 'LEVEL: EXECUTIVE',
      'title': 'ADMINISTRATOR',
      'description':
          'Manage clinical operations, staff analytics, and financial performance oversight.',
      'buttonText': 'SELECT ADMIN',
      'image': AssetResources.admin,
    },
    {
      'id': '2',
      'level': 'LEVEL: OPERATIONS',
      'title': 'RECEPTIONIST',
      'description':
          'Coordinate guest experiences, scheduling, and frontline patient relations.',
      'buttonText': 'SELECT RECEPTIONIST',
      'image': AssetResources.receptionist,
    },
    {
      'id': '3',
      'level': 'LEVEL: PRACTITIONER',
      'title': 'THERAPIST',
      'description':
          'Access treatment protocols, patient histories, and session management tools.',
      'buttonText': 'SELECT THERAPIST',
      'image': AssetResources.therapist,
    },
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => RoleCubit(),
      child: Scaffold(
        backgroundColor: ColorResources.blackColor,
        body: SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 32),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.center,
              children: [
                const Text(
                  'SELECT YOUR ROLE',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 28,
                    fontWeight: FontWeight.w300,
                    letterSpacing: 5,
                  ),
                ),
                const SizedBox(height: 12),
                Text(
                  'Choose your workspace to begin the experience',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 14,
                    fontStyle: FontStyle.italic,
                    letterSpacing: 0.3,
                  ),
                ),
                const SizedBox(height: 32),
                Expanded(
                  child: BlocBuilder<RoleCubit, Map<String, dynamic>?>(
                    builder: (context, selectedRole) {
                      return ListView.separated(
                        itemCount: roles.length,
                        separatorBuilder: (_, __) => const SizedBox(height: 24),
                        itemBuilder: (context, index) {
                          final role = roles[index];
                          final isSelected = selectedRole?['id'] == role['id'];
                          return _RoleCard(
                            role: role,
                            isSelected: isSelected,
                            onTap: () =>
                                context.read<RoleCubit>().selectRole(role),
                            onContinue: () {
                              final current =
                                  context.read<RoleCubit>().state ?? role;
                              Get.toNamed(
                                PageRoutes.signInScreen,
                                arguments: current,
                              );
                            },
                          );
                        },
                      );
                    },
                  ),
                ),

                const SizedBox(height: 32),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ── ROLE CARD ───────────────────────────────────────────────
class _RoleCard extends StatelessWidget {
  final Map<String, dynamic> role;
  final bool isSelected;
  final VoidCallback onTap;
  final VoidCallback onContinue;

  const _RoleCard({
    required this.role,
    required this.isSelected,
    required this.onTap,
    required this.onContinue,
  });

  // ── Access label helper ──────────────────────────────────
  String _accessLabel(String level) {
    if (level.contains('EXECUTIVE')) return 'Executive access';
    if (level.contains('OPERATIONS')) return 'Operations access';
    return 'Practitioner access';
  }

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: IntrinsicHeight(
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // ── Golden bar OUTSIDE the card ─────────────
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 4.0),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                width: 3,
                decoration: BoxDecoration(
                  color: isSelected
                      ? ColorResources.primaryColor
                      : Colors.transparent,
                  borderRadius: const BorderRadius.only(
                    topLeft: Radius.circular(12),
                    bottomLeft: Radius.circular(12),
                  ),
                ),
              ),
            ),

            // ── Card body ────────────────────────────────
            Expanded(
              child: Container(
                decoration: BoxDecoration(
                  color: ColorResources.blackColor,
                  border: Border.all(
                    color: ColorResources.borderColor,
                    width: 0.5,
                  ),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    // ── Image + Text row ─────────────────
                    IntrinsicHeight(
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          // Image
                          Container(
                            width: 100,
                            height: 120,
                            decoration: BoxDecoration(
                              color: ColorResources.blackColor,
                              border: Border(
                                right: BorderSide(
                                  color: ColorResources.borderColor,
                                  width: 0.5,
                                ),
                              ),
                            ),
                            child: ClipRRect(
                              borderRadius: const BorderRadius.only(
                                topLeft: Radius.circular(8),
                              ),
                              child: Image.asset(
                                role['image'],
                                fit: BoxFit.cover,
                                errorBuilder: (_, __, ___) => const Icon(
                                  Icons.person_outline,
                                  color: ColorResources.borderColor,
                                  size: 28,
                                ),
                              ),
                            ),
                          ),

                          // Text content
                          Expanded(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                                vertical: 14,
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Text(
                                    role['level'],
                                    style: TextStyle(
                                      fontFamily: 'CormorantGaramond',
                                      color: ColorResources.primaryColor,
                                      fontSize: 10,
                                      fontWeight: FontWeight.w600,
                                      letterSpacing: 2.5,
                                    ),
                                  ),
                                  const SizedBox(height: 4),
                                  Text(
                                    role['title'],
                                    style: const TextStyle(
                                      fontFamily: 'CormorantGaramond',
                                      color: ColorResources.whiteColor,
                                      fontSize: 18,
                                      fontWeight: FontWeight.w400,
                                      letterSpacing: 2,
                                    ),
                                  ),
                                  const SizedBox(height: 5),
                                  Text(
                                    role['description'],
                                    style: TextStyle(
                                      fontFamily: 'CormorantGaramond',
                                      color: ColorResources.liteTextColor,
                                      fontSize: 14,
                                      fontWeight: FontWeight.w600,
                                      fontStyle: FontStyle.italic,
                                      height: 1.5,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),

                    // ── Footer: always visible ───────────
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.symmetric(
                        horizontal: 14,
                        vertical: 10,
                      ),
                      decoration: BoxDecoration(
                        border: Border(
                          top: BorderSide(
                            color: ColorResources.borderColor,
                            width: 0.5,
                          ),
                        ),
                      ),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text(
                            _accessLabel(role['level']),
                            style: const TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.whiteColor,
                              fontSize: 11,
                              fontStyle: FontStyle.italic,
                              fontWeight: FontWeight.w600,
                              letterSpacing: 1,
                            ),
                          ),
                          GestureDetector(
                            onTap: onContinue,
                            child: AnimatedContainer(
                              duration: const Duration(milliseconds: 200),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 14,
                                vertical: 7,
                              ),
                              decoration: BoxDecoration(
                                border: Border.all(
                                  color: isSelected
                                      ? ColorResources.primaryColor
                                      : ColorResources
                                            .borderColor, // muted border when unselected
                                  width: 0.5,
                                ),
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                role['buttonText'],
                                style: TextStyle(
                                  fontFamily: 'CormorantGaramond',
                                  color: isSelected
                                      ? ColorResources.primaryColor
                                      : ColorResources.whiteColor,
                                  fontSize: 10,
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
            ),
          ],
        ),
      ),
    );
  }
}
