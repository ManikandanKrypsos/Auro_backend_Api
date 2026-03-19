import 'package:flutter/material.dart';
import '../../../../../theme/color/color.dart';
import '../../../../../theme/text_style/app_text_style.dart';

class PhotosTab extends StatelessWidget {
  const PhotosTab({super.key});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // ── Upload button ────────────────────────────
          GestureDetector(
            onTap: () {},
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(vertical: 14),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: ColorResources.primaryColor.withOpacity(0.4),
                  width: 0.5,
                ),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Icon(Icons.upload_outlined,
                      color: ColorResources.primaryColor, size: 14),
                  const SizedBox(width: 8),
                  Text('UPLOAD PHOTOS',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 2.0,
                      )),
                ],
              ),
            ),
          ),

          const SizedBox(height: 24),

          Text('BEFORE & AFTER',
              style: AppTextStyles.headingSmall.copyWith(
                fontSize: 11,
                color: ColorResources.liteTextColor,
                letterSpacing: 3.5,
              )),
          const SizedBox(height: 16),

          // ── Session 1 ────────────────────────────────
          _sessionCard(
            treatmentName: 'Detox Face',
            sessionLabel: 'SESSION 1',
            date: '10 Mar 2025',
            uploadedBy: 'Anna Sterling',
            beforePath: 'assets/images/before1.jpg',
            afterPath: 'assets/images/after1.jpg',
          ),

          // ── Session 2 ────────────────────────────────
          _sessionCard(
            treatmentName: 'HydraBalance',
            sessionLabel: 'SESSION 2',
            date: '25 Mar 2025',
            uploadedBy: 'Maria Voss',
            beforePath: 'assets/images/before2.jpg',
            afterPath: 'assets/images/after2.jpg',
          ),

          // ── Session 3 ────────────────────────────────
          _sessionCard(
            treatmentName: 'Detox Face',
            sessionLabel: 'SESSION 3',
            date: '10 Apr 2025',
            uploadedBy: 'Anna Sterling',
            beforePath: 'assets/images/before3.jpg',
            afterPath: 'assets/images/after3.jpg',
          ),

          const SizedBox(height: 24),
        ],
      ),
    );
  }

  Widget _sessionCard({
    required String treatmentName,
    required String sessionLabel,
    required String date,
    required String uploadedBy,
    required String beforePath,
    required String afterPath,
  }) {
    return Container(
      margin: const EdgeInsets.only(bottom: 16),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 12, 14, 12),
            child: Row(
              children: [
                const Icon(Icons.photo_camera_outlined,
                    color: ColorResources.primaryColor, size: 14),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(treatmentName,
                      style: const TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.whiteColor,
                        fontSize: 15,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 0.5,
                      )),
                ),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: ColorResources.primaryColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(4),
                    border: Border.all(
                        color: ColorResources.primaryColor.withOpacity(0.3),
                        width: 0.5),
                  ),
                  child: Text(sessionLabel,
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: ColorResources.primaryColor,
                        fontSize: 9,
                        fontWeight: FontWeight.w700,
                        letterSpacing: 1.2,
                      )),
                ),
              ],
            ),
          ),

          Divider(
              color: ColorResources.borderColor, height: 1, thickness: 0.5),

          // Photo pair
          Padding(
            padding: const EdgeInsets.all(14),
            child: Row(
              children: [
                Expanded(child: _photoBox('BEFORE', beforePath, false)),
                const SizedBox(width: 10),
                Expanded(child: _photoBox('AFTER', afterPath, true)),
              ],
            ),
          ),

          // Meta
          Padding(
            padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
            child: Row(
              children: [
                Icon(Icons.calendar_today_outlined,
                    color: ColorResources.liteTextColor, size: 11),
                const SizedBox(width: 5),
                Text(date,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor,
                      fontSize: 11,
                    )),
                const SizedBox(width: 14),
                Icon(Icons.person_outline,
                    color: ColorResources.liteTextColor, size: 11),
                const SizedBox(width: 5),
                Text(uploadedBy,
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 11,
                      fontStyle: FontStyle.italic,
                    )),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _photoBox(String label, String path, bool isAfter) {
    final labelColor = isAfter
        ? ColorResources.positiveColor
        : ColorResources.liteTextColor;
    final borderColor = isAfter
        ? ColorResources.positiveColor.withOpacity(0.4)
        : ColorResources.borderColor;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(label,
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: labelColor,
              fontSize: 10,
              fontWeight: FontWeight.w700,
              letterSpacing: 2.0,
            )),
        const SizedBox(height: 6),
        AspectRatio(
          aspectRatio: 3 / 4,
          child: Container(
            decoration: BoxDecoration(
              color: ColorResources.blackColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: borderColor, width: 0.5),
            ),
            child: ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: Image.asset(
                path,
                fit: BoxFit.cover,
                errorBuilder: (_, __, ___) => Center(
                  child: Icon(Icons.image_outlined,
                      color: ColorResources.borderColor, size: 28),
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}