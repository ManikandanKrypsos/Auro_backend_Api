import 'package:aura/app/routes/names.dart';
import 'package:aura/app/widgets/add_button.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';

import '../../../../theme/color/color.dart';
import '../../../../theme/text_style/app_text_style.dart';
import '../../../../widgets/app_search_bar.dart';
import '../../../../widgets/custom_appbar.dart';

class PaymentListScreen extends StatefulWidget {
  const PaymentListScreen({super.key});

  @override
  State<PaymentListScreen> createState() => _PaymentListScreenState();
}

class _PaymentListScreenState extends State<PaymentListScreen> {
  int _selectedTab = 0;
  final TextEditingController _searchController = TextEditingController();
  String _searchQuery = '';

  static const _tabs = ['ALL', 'PAID', 'PENDING'];

  // ── Static Data ───────────────────────────────────────
  final List<Map<String, dynamic>> _payments = const [
    {
      'name': 'Eleanor Vance',
      'service': 'Signature Gold Facial',
      'date': 'OCT 24, 2024',
      'amount': '\$250.00',
      'status': 'PAID',
    },
    {
      'name': 'Julian Sterling',
      'service': 'Deep Tissue Therapy',
      'date': 'OCT 23, 2024',
      'amount': '\$185.00',
      'status': 'PENDING',
    },
    {
      'name': 'Margot Fontaine',
      'service': 'Vitamin C Infusion',
      'date': 'OCT 22, 2024',
      'amount': '\$320.00',
      'status': 'PAID',
    },
    {
      'name': 'Sebastian Thorne',
      'service': 'Sculptural Face Lift',
      'date': 'OCT 21, 2024',
      'amount': '\$450.00',
      'status': 'PAID',
    },
    {
      'name': 'Isabelle Morel',
      'service': 'Hydra-Facial Platinum',
      'date': 'OCT 20, 2024',
      'amount': '\$310.00',
      'status': 'PENDING',
    },
    {
      'name': 'Damien Cross',
      'service': 'Botox — Full Face',
      'date': 'OCT 19, 2024',
      'amount': '\$680.00',
      'status': 'PAID',
    },
  ];

  // ── Filter ────────────────────────────────────────────
  List<Map<String, dynamic>> get _filteredPayments {
    List<Map<String, dynamic>> items;
    switch (_selectedTab) {
      case 1:
        items = _payments.where((p) => p['status'] == 'PAID').toList();
        break;
      case 2:
        items = _payments.where((p) => p['status'] == 'PENDING').toList();
        break;
      default:
        items = _payments;
    }
    if (_searchQuery.isNotEmpty) {
      items = items
          .where((p) => (p['name'] as String)
              .toLowerCase()
              .contains(_searchQuery.toLowerCase()))
          .toList();
    }
    return items;
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: ColorResources.blackColor,
      appBar: const CustomAppBar(title: 'PAYMENTS'),
      body: SafeArea(
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 16),

            // ── Search ──
            AppSearchBar(
              hintText: 'Search by patient name...',
              controller: _searchController,
              onChanged: (v) => setState(() => _searchQuery = v),
            ),
            const SizedBox(height: 12),

            // ── Sort Row ──
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 0, 20, 8),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.end,
                children: [
                  Text(
                    'SORT BY DATE',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.6),
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2,
                    ),
                  ),
                  const SizedBox(width: 4),
                  Icon(
                    Icons.swap_vert_rounded,
                    color: ColorResources.liteTextColor.withOpacity(0.6),
                    size: 14,
                  ),
                ],
              ),
            ),
            _buildTabRow(),
            const SizedBox(height: 16),

            Expanded(
              child: _filteredPayments.isEmpty
                  ? Center(
                      child: Text(
                        'NO PAYMENTS FOUND',
                        style: AppTextStyles.headingSmall.copyWith(
                          color:
                              ColorResources.liteTextColor.withOpacity(0.4),
                          letterSpacing: 3,
                        ),
                      ),
                    )
                  : ListView.separated(
                      padding: const EdgeInsets.fromLTRB(20, 4, 20, 40),
                      itemCount: _filteredPayments.length,
                      separatorBuilder: (_, __) =>
                          const SizedBox(height: 12),
                      itemBuilder: (_, i) =>
                          _buildPaymentCard(_filteredPayments[i]),
                    ),
            ),
          ],
        ),
      ),
      floatingActionButton: AddButton(onTap: (){
        Get.toNamed(PageRoutes.addEditPaymentScreen);
      }),
    );
  }

  // ── Tab Row ───────────────────────────────────────────
  Widget _buildTabRow() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.center,
        children: List.generate(_tabs.length, (i) {
          final isSelected = _selectedTab == i;
          return GestureDetector(
            onTap: () => setState(() => _selectedTab = i),
            child: Padding(
              padding:
                  EdgeInsets.only(right: i < _tabs.length - 1 ? 40 : 0),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    _tabs[i],
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: isSelected
                          ? ColorResources.primaryColor
                          : ColorResources.liteTextColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 2.5,
                    ),
                  ),
                  const SizedBox(height: 6),
                  AnimatedContainer(
                    duration: const Duration(milliseconds: 200),
                    height: 1.5,
                    width: isSelected ? _tabs[i].length * 10.0 : 0,
                    color: ColorResources.primaryColor,
                  ),
                ],
              ),
            ),
          );
        }),
      ),
    );
  }

  // ── Payment Card ──────────────────────────────────────
  Widget _buildPaymentCard(Map<String, dynamic> payment) {
    final bool isPaid = payment['status'] == 'PAID';

    return GestureDetector(
      onTap: () => Get.toNamed(PageRoutes.paymentDetailScreen),
      child: Container(
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 14),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  payment['name'] as String,
                  style: const TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.whiteColor,
                    fontSize: 18,
                    fontWeight: FontWeight.w500,
                    letterSpacing: 0.2,
                  ),
                ),
                Text(
                  payment['amount'] as String,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: isPaid
                        ? ColorResources.whiteColor
                        : ColorResources.primaryColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 0.5,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 2),
            Text(
              payment['service'] as String,
              style: AppTextStyles.bodyItalic.copyWith(fontSize: 12),
            ),
            const SizedBox(height: 12),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  payment['date'] as String,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.liteTextColor.withOpacity(0.55),
                    fontSize: 11,
                    letterSpacing: 1.2,
                  ),
                ),
                _buildStatusBadge(isPaid: isPaid),
              ],
            ),
          ],
        ),
      ),
    );
  }

  // ── Status Badge ──────────────────────────────────────
  Widget _buildStatusBadge({required bool isPaid}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 5),
      decoration: BoxDecoration(
        color: isPaid
            ? ColorResources.cardColor
            : ColorResources.primaryColor.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
          color: isPaid
              ? ColorResources.borderColor
              : ColorResources.primaryColor.withOpacity(0.4),
          width: 0.5,
        ),
      ),
      child: Text(
        isPaid ? 'PAID' : 'PENDING',
        style: TextStyle(
          fontFamily: 'CormorantGaramond',
          color: isPaid
              ? ColorResources.liteTextColor
              : ColorResources.primaryColor,
          fontSize: 9,
          fontWeight: FontWeight.w700,
          letterSpacing: 1.5,
        ),
      ),
    );
  }
}