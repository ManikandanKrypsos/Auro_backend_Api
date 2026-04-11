import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../theme/color/color.dart';
import '../../../admin/patient/view/patient_list_screen.dart';
import '../../../admin/payemt/view/payment_list_screen.dart';
import '../../Appointments/view/Appointment_list_screen.dart';
import '../../dashboard/view/receptionist_dashboard.dart';
import '../../settings/receptionist_setting_screen.dart';
import '../cubit/receptionist_nav_cubit.dart';
import '../view/receptionist_bottom_nav_bar.dart';

class ReceptionistMainScreen extends StatelessWidget {
  const ReceptionistMainScreen({super.key});

  static const _pages = <Widget>[
    ReceptionistDashboard(),
    AppointmentListScreen(),
    PatientsScreen(),
    PaymentListScreen(),
    ReceptionistSettingsScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ReceptionistNavCubit(),
      child: BlocBuilder<ReceptionistNavCubit, ReceptionistNavState>(
        builder: (context, state) {
          return Scaffold(
            backgroundColor: const Color(0xFF0A0A0A),
            body: IndexedStack(
              index: state.activeTab.index,
              children: _pages,
            ),
            bottomNavigationBar: const ReceptionistBottomNavBar(),
          );
        },
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
