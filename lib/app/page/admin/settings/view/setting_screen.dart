import 'package:aura/app/widgets/alert_button.dart';
import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';
import 'package:get/get_core/src/get_main.dart';
import 'package:get/get_navigation/get_navigation.dart';
import '../../../../routes/names.dart';
import '../../../../theme/color/color.dart';

class AdminSettingsScreen extends StatelessWidget {
  const AdminSettingsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: const CustomAppBar(title: 'SETTINGS'),
      body: SafeArea(
        child: ListView(
          padding: EdgeInsets.zero,
          children: [                  // ── Quick Access Grid ───────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _SectionLabel('OPERATIONS'),
                  const SizedBox(height: 12),
                  GridView.count(
                    crossAxisCount: 2,
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    crossAxisSpacing: 12,
                    mainAxisSpacing: 12,
                    childAspectRatio: 1.45,
                    children: [
                      _QuickCard(
                        icon: Icons.category_outlined,
                        label: 'Services',
                        subtitle: 'Manage offerings',
                        onTap: () => Get.toNamed(PageRoutes.serviceListScreen),
                      ),
                      _QuickCard(
                        icon: Icons.meeting_room_outlined,
                        label: 'Rooms',
                        subtitle: 'Configure spaces',
                        onTap: () => Get.toNamed(PageRoutes.roomListScreen),
                      ),
                      _QuickCard(
                        icon: Icons.local_hospital_outlined,
                        label: 'Clinic Ops',
                        subtitle: 'Daily operations',
                        onTap: () => Get.toNamed(PageRoutes.clinicOperation),
                      ),
                      _QuickCard(
                        icon: Icons.inventory_2_outlined,
                        label: 'Payments',
                        subtitle: 'Manage payments',
                        onTap: () => Get.toNamed(PageRoutes.paymentListScreen),
                      ),
                    ],
                  ),

                  const SizedBox(height: 36),

                  // ── Automation Section ──────────────────
                  _SectionLabel('AUTOMATION & AI'),
                  const SizedBox(height: 12),
                  _SettingsGroup(
                    items: [
                      _SettingTile(
                        icon: Icons.bolt_outlined,
                        label: 'Automation',
                        subtitle: 'Rules & triggers',
                      ),
                      _SettingTile(
                        icon: Icons.auto_awesome_outlined,
                        label: 'AI Assistant',
                        subtitle: 'Smart suggestions',
                      ),
                    ],
                  ),

                  const SizedBox(height: 36),

                  // ── Clinic & Account ────────────────────
                  _SectionLabel('PREFERENCES'),
                  const SizedBox(height: 12),
                  _SettingsGroup(
                    items: [
                      _SettingTile(
                        icon: Icons.tune_outlined,
                        label: 'Clinic Settings',
                        subtitle: 'Branding & configuration',
                      ),
                      _SettingTile(
                        icon: Icons.person_outline,
                        label: 'My Profile',
                        subtitle: 'Account & personal info',
                      ),
                      _SettingTile(
                        icon: Icons.notifications_outlined,
                        label: 'Notifications',
                        subtitle: 'Alerts & reminders',
                      ),
                    ],
                  ),

                  const SizedBox(height: 40),

                  // ── Log Out ─────────────────────────────
                  AlertButton(onTap: () {}, text: 'LOG OUT'),

                  const SizedBox(height: 36),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}



// ── SECTION LABEL ──────────────────────────────────────────
class _SectionLabel extends StatelessWidget {
  final String text;
  const _SectionLabel(this.text);

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: TextStyle(
        fontFamily: 'CormorantGaramond',
        color: ColorResources.liteTextColor.withOpacity(0.5),
        fontSize: 11,
        fontWeight: FontWeight.w600,
        letterSpacing: 3.0,
      ),
    );
  }
}

// ── QUICK ACCESS CARD (Grid) ───────────────────────────────
class _QuickCard extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback? onTap;

  const _QuickCard({
    required this.icon,
    required this.label,
    required this.subtitle,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Container(
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Icon container
            Container(
              width: 38,
              height: 38,
              decoration: BoxDecoration(
                color: ColorResources.primaryColor.withOpacity(0.1),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: ColorResources.primaryColor.withOpacity(0.25),
                  width: 0.5,
                ),
              ),
              child: Icon(icon, color: ColorResources.primaryColor, size: 18),
            ),

            const Spacer(),

            Text(
              label,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 17,
                fontWeight: FontWeight.w300,
                letterSpacing: 0.3,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              subtitle,
              style: TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.liteTextColor.withOpacity(0.45),
                fontSize: 11,
                fontWeight: FontWeight.w400,
                letterSpacing: 0.3,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── SETTINGS GROUP (List) ──────────────────────────────────
class _SettingsGroup extends StatelessWidget {
  final List<_SettingTile> items;
  const _SettingsGroup({required this.items});

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        children: List.generate(items.length, (i) {
          return Column(
            children: [
              items[i],
              if (i < items.length - 1)
                Divider(
                  color: ColorResources.borderColor,
                  height: 1,
                  thickness: 0.5,
                  indent: 62,
                  endIndent: 0,
                ),
            ],
          );
        }),
      ),
    );
  }
}

// ── SETTING TILE ───────────────────────────────────────────
class _SettingTile extends StatelessWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final VoidCallback? onTap;

  const _SettingTile({
    required this.icon,
    required this.label,
    required this.subtitle,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
        child: Row(
          children: [
            // Tinted icon box
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: ColorResources.primaryColor.withOpacity(0.08),
                borderRadius: BorderRadius.circular(9),
                border: Border.all(
                  color: ColorResources.primaryColor.withOpacity(0.2),
                  width: 0.5,
                ),
              ),
              child: Icon(
                icon,
                color: ColorResources.primaryColor,
                size: 17,
              ),
            ),

            const SizedBox(width: 14),

            // Text
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    label,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 18,
                      fontWeight: FontWeight.w300,
                      letterSpacing: 0.3,
                    ),
                  ),
                  Text(
                    subtitle,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.45),
                      fontSize: 12,
                      fontWeight: FontWeight.w400,
                    ),
                  ),
                ],
              ),
            ),

            Icon(
              Icons.chevron_right,
              color: ColorResources.liteTextColor.withOpacity(0.35),
              size: 18,
            ),
          ],
        ),
      ),
    );
  }
}
