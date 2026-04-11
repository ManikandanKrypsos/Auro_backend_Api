import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../routes/names.dart';
import '../../../theme/color/color.dart';
import '../../../widgets/alert_button.dart';

class ReceptionistSettingsScreen extends StatelessWidget {
  const ReceptionistSettingsScreen({super.key});
  @override
  Widget build(BuildContext context) => Scaffold(
    appBar: CustomAppBar(title: "SETTINGS"),
    body: Padding(
      padding: const EdgeInsets.all(16.0),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          _SectionLabel('PREFERENCES'),
          const SizedBox(height: 12),
          _SettingsGroup(
            items: [
              _SettingTile(
                icon: Icons.person_outline,
                label: 'My Profile',
                subtitle: 'Account & personal info',
              ),
              _SettingTile(
                icon: Icons.notifications_none_outlined,
                label: 'Notifications',
                subtitle: 'Manage alerts',
              ),
            ],
          ),

          const SizedBox(height: 32),

          _SectionLabel('CLINIC'),
          const SizedBox(height: 12),
          _ClinicInfoCard(),

          const SizedBox(height: 32),

          Spacer(),

          // ── Log Out ─────────────────────────────
          AlertButton(
            onTap: () {
              Get.offAllNamed(PageRoutes.selectRoleScreen);
            },
            text: 'LOG OUT',
          ),

          const SizedBox(height: 36),
        ],
      ),
    ),
  );
}

// ── CLINIC INFO CARD ───────────────────────────────────────
class _ClinicInfoCard extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: ColorResources.primaryColor.withOpacity(0.2),
          width: 0.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.2),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                "A U R A",
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 20,
                  fontWeight: FontWeight.w600,
                  letterSpacing: 4,
                ),
              ),
              Icon(
                Icons.verified_user_outlined,
                color: ColorResources.primaryColor.withOpacity(0.5),
                size: 18,
              ),
            ],
          ),
          const SizedBox(height: 16),
          _ClinicDetailRow(icon: Icons.location_on_outlined, text: "MG Road, Kochi, Kerala"),
          const SizedBox(height: 10),
          _ClinicDetailRow(icon: Icons.phone_outlined, text: "+91 98765 43210"),
          const SizedBox(height: 10),
          _ClinicDetailRow(icon: Icons.access_time_outlined, text: "Mon - Sat : 9:00 AM - 6:00 PM"),
        ],
      ),
    );
  }
}

class _ClinicDetailRow extends StatelessWidget {
  final IconData icon;
  final String text;
  const _ClinicDetailRow({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, size: 14, color: ColorResources.liteTextColor.withOpacity(0.4)),
        const SizedBox(width: 10),
        Expanded(
          child: Text(
            text,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.8),
              fontSize: 14,
              letterSpacing: 0.3,
            ),
          ),
        ),
      ],
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
              child: Icon(icon, color: ColorResources.primaryColor, size: 17),
            ),
            const SizedBox(width: 14),
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
