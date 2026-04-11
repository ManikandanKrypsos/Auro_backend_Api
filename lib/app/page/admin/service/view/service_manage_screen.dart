import 'package:aura/app/widgets/custom_appbar.dart';
import 'package:aura/app/widgets/custom_textform_lables.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:aura/app/widgets/app_drop_down.dart';
import 'package:aura/app/widgets/primary_button.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../../../theme/color/color.dart';
import '../cubit/service_manage_cubit.dart';

// ── Static options ─────────────────────────────────────────
const List<String> _roomTypes = [
  'Therapy Suite A',
  'Therapy Suite B',
  'Laser Room',
  'Relaxation Room',
];

const List<String> _equipmentOptions = [
  'LASER L24',
  'Microneedling Device',
  'Ultrasound Probe',
  'Dermaplaning Tool',
  'LED Light Panel',
];

const List<String> _consumableOptions = [
  'SERUM',
  'MASK',
  'EXFOLIANT',
  'TONER',
  'MOISTURISER',
  'SPF CREAM',
];

const List<String> _contraindicationOptions = [
  'Pregnancy',
  'Active Infection',
  'Recent Surgery',
  'Blood Thinners',
  'Sunburn',
  'Open Wounds',
  'Autoimmune Condition',
];

const List<String> _therapistOptions = [
  'Elena Sterling',
  'Aria Dance',
  'Maya Ross',
  'Jade Kim',
];

const List<String> _freqUnits = ['Days', 'Weeks', 'Months'];
const List<int> _quickNumbers = [1, 2, 3, 4, 5, 6, 8, 10, 12];

// ── Screen ─────────────────────────────────────────────────
class ServiceManageScreen extends StatelessWidget {
  final Map<String, dynamic>? service;
  const ServiceManageScreen({super.key, this.service});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (_) => ServiceManageCubit(service: service),
      child: _ServiceManageBody(service: service),
    );
  }
}

// ── Body ───────────────────────────────────────────────────
class _ServiceManageBody extends StatefulWidget {
  final Map<String, dynamic>? service;
  const _ServiceManageBody({this.service});

  @override
  State<_ServiceManageBody> createState() => _ServiceManageBodyState();
}

class _ServiceManageBodyState extends State<_ServiceManageBody> {
  late final TextEditingController _nameCtrl;
  late final TextEditingController _descCtrl;
  late final TextEditingController _durationCtrl;
  late final TextEditingController _priceCtrl;
  final TextEditingController _preCareCtrl    = TextEditingController();
  final TextEditingController _postCareCtrl   = TextEditingController();
  final TextEditingController _freqNumberCtrl = TextEditingController(text: '1');
  final TextEditingController _packageCtrl    = TextEditingController(text: '6');

  @override
  void initState() {
    super.initState();
    final s = widget.service;
    _nameCtrl     = TextEditingController(text: s?['name'] as String? ?? '');
    _descCtrl     = TextEditingController(text: s?['description'] as String? ?? '');
    _durationCtrl = TextEditingController(
        text: s != null ? (s['duration'] as int? ?? 0).toString() : '');
    _priceCtrl    = TextEditingController(
        text: s != null ? (s['price'] as double? ?? 0.0).toStringAsFixed(2) : '');
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _descCtrl.dispose();
    _durationCtrl.dispose();
    _priceCtrl.dispose();
    _preCareCtrl.dispose();
    _postCareCtrl.dispose();
    _freqNumberCtrl.dispose();
    _packageCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.service != null;
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: CustomAppBar(
          title: isEditing ? 'EDIT SERVICE' : 'ADD NEW SERVICE'),
      body: SingleChildScrollView(
        padding: const EdgeInsets.only(bottom: 40),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _SectionHeader(icon: Icons.category_outlined,          text: 'BASIC INFO'),
            _BasicInfoSection(
              nameCtrl:     _nameCtrl,
              descCtrl:     _descCtrl,
              durationCtrl: _durationCtrl,
              priceCtrl:    _priceCtrl,
            ),
            _SectionHeader(icon: Icons.medical_services_outlined,  text: 'TREATMENT PROTOCOL'),
            _TreatmentProtocolSection(
              preCareCtrl:  _preCareCtrl,
              postCareCtrl: _postCareCtrl,
            ),
            _SectionHeader(icon: Icons.event_repeat_outlined,      text: 'SESSION RECOMMENDATION'),
            _SessionSection(
              freqNumberCtrl: _freqNumberCtrl,
              packageCtrl:    _packageCtrl,
            ),
            _SectionHeader(icon: Icons.inventory_2_outlined,       text: 'RESOURCES'),
            const _ResourcesSection(),
            _SectionHeader(icon: Icons.people_outline,             text: 'STAFF ASSIGNMENT'),
            const _StaffSection(),
            _SectionHeader(icon: Icons.perm_media_outlined,        text: 'MEDIA'),
            const _MediaSection(),
            const SizedBox(height: 32),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: PrimaryButton(label: 'SAVE SERVICE', onTap: () {}),
            ),
            const SizedBox(height: 12),
            Center(
              child: TextButton(
                onPressed: () => Navigator.pop(context),
                child: Text(
                  'CANCEL & DISCARD',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    fontSize: 11,
                    letterSpacing: 2,
                    color: ColorResources.whiteColor.withOpacity(0.35),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ── SECTION HEADER ─────────────────────────────────────────
class _SectionHeader extends StatelessWidget {
  final IconData icon;
  final String text;
  const _SectionHeader({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(20, 28, 20, 20),
      child: Row(
        children: [
          Icon(icon, color: ColorResources.primaryColor, size: 18),
          const SizedBox(width: 12),
          Text(
            text,
            style: const TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 15,
              fontWeight: FontWeight.w600,
              letterSpacing: 3.5,
            ),
          ),
        ],
      ),
    );
  }
}

// ── BASIC INFO ─────────────────────────────────────────────
class _BasicInfoSection extends StatelessWidget {
  final TextEditingController nameCtrl;
  final TextEditingController descCtrl;
  final TextEditingController durationCtrl;
  final TextEditingController priceCtrl;

  const _BasicInfoSection({
    required this.nameCtrl,
    required this.descCtrl,
    required this.durationCtrl,
    required this.priceCtrl,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CustomLabel(text: 'SERVICE NAME'),
          CustomTextField(controller: nameCtrl, hint: 'Detox / Glow'),

          const SizedBox(height: 20),
          const CustomLabel(text: 'CATEGORY'),
          const _CategoryToggle(),

          const SizedBox(height: 20),
          const CustomLabel(text: 'DESCRIPTION'),
          CustomTextField(
            controller: descCtrl,
            hint: 'Describe the therapeutic benefits...',
            maxLine: 4,
          ),

          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const CustomLabel(text: 'DURATION (MIN)'),
                    CustomTextField(
                      controller: durationCtrl,
                      hint: '60',
                      keyboardType: TextInputType.number,
                    ),
                  ],
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const CustomLabel(text: 'PRICE (\$)'),
                    CustomTextField(
                      controller: priceCtrl,
                      hint: '150.00',
                      keyboardType: TextInputType.number,
                    ),
                  ],
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

// ── CATEGORY TOGGLE ────────────────────────────────────────
class _CategoryToggle extends StatelessWidget {
  const _CategoryToggle();

  @override
  Widget build(BuildContext context) {
    return BlocBuilder<ServiceManageCubit, ServiceManageState>(
      buildWhen: (p, c) => p.categoryTab != c.categoryTab,
      builder: (context, state) {
        return Row(
          children: [
            _radio(context, 'FACE', 0, state.categoryTab),
            _radio(context, 'BODY', 1, state.categoryTab),
          ],
        );
      },
    );
  }

  Widget _radio(BuildContext ctx, String label, int idx, int selected) {
    final on = selected == idx;
    return Expanded(
      child: GestureDetector(
        onTap: () => ctx.read<ServiceManageCubit>().selectCategory(idx),
        child: Padding(
          padding: const EdgeInsets.only(top: 8),
          child: Row(
            children: [
              Container(
                width: 18, height: 18,
                decoration: BoxDecoration(
                  shape: BoxShape.circle,
                  border: Border.all(
                    color: on
                        ? ColorResources.primaryColor
                        : ColorResources.whiteColor.withOpacity(0.3),
                    width: 1.5,
                  ),
                ),
                child: on
                    ? Center(
                        child: Container(
                          width: 9, height: 9,
                          decoration: const BoxDecoration(
                            shape: BoxShape.circle,
                            color: ColorResources.primaryColor,
                          ),
                        ),
                      )
                    : null,
              ),
              const SizedBox(width: 10),
              Text(label,
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 2.5,
                    color: on
                        ? ColorResources.primaryColor
                        : ColorResources.whiteColor.withOpacity(0.5),
                  )),
            ],
          ),
        ),
      ),
    );
  }
}

// ── TREATMENT PROTOCOL ─────────────────────────────────────
class _TreatmentProtocolSection extends StatelessWidget {
  final TextEditingController preCareCtrl;
  final TextEditingController postCareCtrl;

  const _TreatmentProtocolSection({
    required this.preCareCtrl,
    required this.postCareCtrl,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CustomLabel(text: 'PRE-CARE INSTRUCTIONS'),
          CustomTextField(
              controller: preCareCtrl,
              hint: 'Avoid sun exposure 24h prior...',
              maxLine: 3),

          const SizedBox(height: 20),
          const CustomLabel(text: 'POST-CARE INSTRUCTIONS'),
          CustomTextField(
              controller: postCareCtrl,
              hint: 'Apply SPF 50 daily...',
              maxLine: 3),

          const SizedBox(height: 20),
          const CustomLabel(text: 'CONTRAINDICATIONS'),
          BlocBuilder<ServiceManageCubit, ServiceManageState>(
            buildWhen: (p, c) => p.contraindications != c.contraindications,
            builder: (context, state) {
              final cubit = context.read<ServiceManageCubit>();
              return Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Expanded(
                        child: AppDropdown(
                          hint: 'Select contraindication...',
                          items: _contraindicationOptions,
                          onChanged: (v) {
                            if (v != null) cubit.addContraindication(v);
                          },
                        ),
                      ),
                      const SizedBox(width: 10),
                      GestureDetector(
                        onTap: () => _showAddDialog(
                          context,
                          'Add Contraindication',
                          cubit.addContraindication,
                        ),
                        child: Container(
                          height: 48, width: 48,
                          decoration: BoxDecoration(
                            color: ColorResources.primaryColor,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Icon(Icons.add,
                              color: Colors.black, size: 20),
                        ),
                      ),
                    ],
                  ),
                  if (state.contraindications.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    _TagList(
                      tags: state.contraindications,
                      onRemove: cubit.removeContraindication,
                    ),
                  ],
                ],
              );
            },
          ),
        ],
      ),
    );
  }
}

// ── SESSION ────────────────────────────────────────────────
class _SessionSection extends StatelessWidget {
  final TextEditingController freqNumberCtrl;
  final TextEditingController packageCtrl;

  const _SessionSection({
    required this.freqNumberCtrl,
    required this.packageCtrl,
  });

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const CustomLabel(text: 'FREQUENCY'),
          BlocBuilder<ServiceManageCubit, ServiceManageState>(
            buildWhen: (p, c) => p.freqUnit != c.freqUnit,
            builder: (context, state) {
              return Row(
                children: [
                  Expanded(
                    flex: 2,
                    child: _NumberPickerField(
                      controller: freqNumberCtrl,
                      quickNumbers: _quickNumbers,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 3,
                    child: AppDropdown(
                      value: state.freqUnit,
                      items: _freqUnits,
                      onChanged: (v) {
                        if (v != null)
                          context.read<ServiceManageCubit>().selectFreqUnit(v);
                      },
                    ),
                  ),
                ],
              );
            },
          ),

          const SizedBox(height: 20),
          const CustomLabel(text: 'PACKAGE SESSIONS'),
          _NumberPickerField(
            controller: packageCtrl,
            quickNumbers: _quickNumbers,
          ),
        ],
      ),
    );
  }
}

// ── RESOURCES ──────────────────────────────────────────────
class _ResourcesSection extends StatelessWidget {
  const _ResourcesSection();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: BlocBuilder<ServiceManageCubit, ServiceManageState>(
        builder: (context, state) {
          final cubit = context.read<ServiceManageCubit>();
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const CustomLabel(text: 'ROOM TYPE'),
              AppDropdown(
                value: state.roomType,
                items: _roomTypes,
                onChanged: (v) { if (v != null) cubit.selectRoom(v); },
              ),

              const SizedBox(height: 20),
              const CustomLabel(text: 'EQUIPMENT'),
              AppDropdown(
                hint: 'Select equipment...',
                items: _equipmentOptions,
                onChanged: (v) { if (v != null) cubit.addEquipment(v); },
              ),
              if (state.equipmentTags.isNotEmpty) ...[
                const SizedBox(height: 12),
                _TagList(tags: state.equipmentTags, onRemove: cubit.removeEquipment),
              ],

              const SizedBox(height: 20),
              const CustomLabel(text: 'CONSUMABLES'),
              AppDropdown(
                hint: 'Select consumable...',
                items: _consumableOptions,
                onChanged: (v) { if (v != null) cubit.addConsumable(v); },
              ),
              if (state.consumableTags.isNotEmpty) ...[
                const SizedBox(height: 12),
                _TagList(tags: state.consumableTags, onRemove: cubit.removeConsumable),
              ],
            ],
          );
        },
      ),
    );
  }
}

// ── STAFF ──────────────────────────────────────────────────
class _StaffSection extends StatelessWidget {
  const _StaffSection();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: BlocBuilder<ServiceManageCubit, ServiceManageState>(
        buildWhen: (p, c) => p.assignedStaff != c.assignedStaff,
        builder: (context, state) {
          final cubit = context.read<ServiceManageCubit>();
          return Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              AppDropdown(
                hint: 'Select therapist...',
                items: _therapistOptions,
                onChanged: (v) { if (v != null) cubit.addStaff(v); },
              ),
              const SizedBox(height: 16),
              ...state.assignedStaff.map((name) => _StaffRow(
                    name: name,
                    onRemove: () => cubit.removeStaff(name),
                  )),
            ],
          );
        },
      ),
    );
  }
}

class _StaffRow extends StatelessWidget {
  final String name;
  final VoidCallback onRemove;
  const _StaffRow({required this.name, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    final initials =
        name.split(' ').take(2).map((w) => w[0].toUpperCase()).join();
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        children: [
          Container(
            width: 34, height: 34,
            decoration: BoxDecoration(
              color: ColorResources.primaryColor.withOpacity(0.2),
              shape: BoxShape.circle,
              border: Border.all(
                  color: ColorResources.primaryColor, width: 0.8),
            ),
            alignment: Alignment.center,
            child: Text(initials,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                )),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: Text(name,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 14,
                )),
          ),
          GestureDetector(
            onTap: onRemove,
            child: Icon(Icons.close,
                size: 16,
                color: ColorResources.whiteColor.withOpacity(0.4)),
          ),
        ],
      ),
    );
  }
}

// ── MEDIA ──────────────────────────────────────────────────
class _MediaSection extends StatelessWidget {
  const _MediaSection();

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: GestureDetector(
        onTap: () {},
        child: Container(
          height: 120,
          decoration: BoxDecoration(
            color: ColorResources.cardColor,
            borderRadius: BorderRadius.circular(10),
            border: Border.all(color: ColorResources.borderColor, width: 0.5),
          ),
          child: Center(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.add_photo_alternate_outlined,
                    color: ColorResources.primaryColor.withOpacity(0.7),
                    size: 28),
                const SizedBox(height: 8),
                Text('UPLOAD SERVICE IMAGE',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor.withOpacity(0.5),
                      fontSize: 11,
                      letterSpacing: 2,
                      fontWeight: FontWeight.w600,
                    )),
                const SizedBox(height: 4),
                Text('PNG, JPG up to 10MB',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor.withOpacity(0.25),
                      fontSize: 11,
                    )),
              ],
            ),
          ),
        ),
      ),
    );
  }
}

// ── TAG LIST ───────────────────────────────────────────────
class _TagList extends StatelessWidget {
  final List<String> tags;
  final ValueChanged<String> onRemove;
  const _TagList({required this.tags, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 10,
      runSpacing: 10,
      children: tags.map((t) => _Tag(label: t, onRemove: () => onRemove(t))).toList(),
    );
  }
}

class _Tag extends StatelessWidget {
  final String label;
  final VoidCallback onRemove;
  const _Tag({required this.label, required this.onRemove});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.fromLTRB(10, 6, 6, 6),
      decoration: BoxDecoration(
        color: ColorResources.primaryColor.withOpacity(0.12),
        borderRadius: BorderRadius.circular(6),
        border: Border.all(
            color: ColorResources.primaryColor.withOpacity(0.4), width: 0.5),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Text(label,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.primaryColor,
                fontSize: 11,
                fontWeight: FontWeight.w600,
                letterSpacing: 1.5,
              )),
          const SizedBox(width: 6),
          GestureDetector(
            onTap: onRemove,
            child: Icon(Icons.close,
                size: 12,
                color: ColorResources.primaryColor.withOpacity(0.7)),
          ),
        ],
      ),
    );
  }
}

// ── NUMBER PICKER FIELD ────────────────────────────────────
class _NumberPickerField extends StatefulWidget {
  final TextEditingController controller;
  final List<int> quickNumbers;
  const _NumberPickerField(
      {required this.controller, required this.quickNumbers});

  @override
  State<_NumberPickerField> createState() => _NumberPickerFieldState();
}

class _NumberPickerFieldState extends State<_NumberPickerField> {
  final LayerLink _link = LayerLink();
  OverlayEntry? _overlay;
  bool _open = false;

  void _toggle() => _open ? _close() : _openOverlay();

  void _openOverlay() {
    _overlay = OverlayEntry(
      builder: (_) => _NumberOverlay(
        link: _link,
        numbers: widget.quickNumbers,
        onSelect: (n) { widget.controller.text = n.toString(); _close(); },
        onDismiss: _close,
      ),
    );
    Overlay.of(context).insert(_overlay!);
    setState(() => _open = true);
  }

  void _close() {
    _overlay?.remove();
    _overlay = null;
    if (mounted) setState(() => _open = false);
  }

  @override
  void dispose() { _close(); super.dispose(); }

  @override
  Widget build(BuildContext context) {
    return CompositedTransformTarget(
      link: _link,
      child: Container(
        height: 48,
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: _open ? ColorResources.primaryColor : ColorResources.borderColor,
            width: _open ? 0.8 : 0.5,
          ),
        ),
        child: Row(
          children: [
            Expanded(
              child: TextField(
                controller: widget.controller,
                keyboardType: TextInputType.number,
                textAlign: TextAlign.center,
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 16,
                  fontWeight: FontWeight.w300,
                ),
                decoration: const InputDecoration(
                  border: InputBorder.none,
                  isDense: true,
                  contentPadding: EdgeInsets.symmetric(horizontal: 12),
                ),
                cursorColor: ColorResources.primaryColor,
              ),
            ),
            Container(width: 0.5, height: 28, color: ColorResources.borderColor),
            GestureDetector(
              onTap: _toggle,
              child: Container(
                width: 38, height: 48,
                alignment: Alignment.center,
                child: AnimatedRotation(
                  turns: _open ? 0.5 : 0,
                  duration: const Duration(milliseconds: 180),
                  child: Icon(Icons.keyboard_arrow_down,
                      size: 20,
                      color: ColorResources.primaryColor.withOpacity(0.8)),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _NumberOverlay extends StatelessWidget {
  final LayerLink link;
  final List<int> numbers;
  final ValueChanged<int> onSelect;
  final VoidCallback onDismiss;
  const _NumberOverlay(
      {required this.link, required this.numbers, required this.onSelect, required this.onDismiss});

  @override
  Widget build(BuildContext context) {
    return Stack(
      children: [
        Positioned.fill(
          child: GestureDetector(
            onTap: onDismiss,
            behavior: HitTestBehavior.translucent,
            child: const SizedBox.expand(),
          ),
        ),
        CompositedTransformFollower(
          link: link,
          showWhenUnlinked: false,
          offset: const Offset(0, 52),
          child: Material(
            color: Colors.transparent,
            child: Container(
              constraints: const BoxConstraints(maxHeight: 220),
              decoration: BoxDecoration(
                color: const Color(0xFF1A1A1A),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(color: ColorResources.borderColor, width: 0.5),
                boxShadow: [
                  BoxShadow(
                      color: Colors.black.withOpacity(0.5),
                      blurRadius: 16,
                      offset: const Offset(0, 4)),
                ],
              ),
              child: ClipRRect(
                borderRadius: BorderRadius.circular(10),
                child: ListView.builder(
                  padding: EdgeInsets.zero,
                  shrinkWrap: true,
                  itemCount: numbers.length,
                  itemBuilder: (_, i) {
                    final n = numbers[i];
                    return InkWell(
                      onTap: () => onSelect(n),
                      overlayColor: WidgetStateProperty.all(
                          ColorResources.primaryColor.withOpacity(0.08)),
                      child: Container(
                        height: 40,
                        alignment: Alignment.center,
                        decoration: BoxDecoration(
                          border: i < numbers.length - 1
                              ? Border(
                                  bottom: BorderSide(
                                      color: ColorResources.borderColor
                                          .withOpacity(0.4),
                                      width: 0.5))
                              : null,
                        ),
                        child: Text(n.toString(),
                            style: const TextStyle(
                              fontFamily: 'CormorantGaramond',
                              color: ColorResources.whiteColor,
                              fontSize: 15,
                              fontWeight: FontWeight.w300,
                            )),
                      ),
                    );
                  },
                ),
              ),
            ),
          ),
        ),
      ],
    );
  }
}

// ── ADD DIALOG ─────────────────────────────────────────────
void _showAddDialog(
    BuildContext context, String title, ValueChanged<String> onConfirm) {
  final ctrl = TextEditingController();
  showDialog(
    context: context,
    builder: (_) => AlertDialog(
      backgroundColor: const Color(0xFF1A1A1A),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
      title: Text(title,
          style: const TextStyle(
            fontFamily: 'CormorantGaramond',
            color: ColorResources.whiteColor,
            fontSize: 16,
            letterSpacing: 2,
          )),
      content: TextField(
        controller: ctrl,
        autofocus: true,
        style: const TextStyle(
            color: ColorResources.whiteColor,
            fontFamily: 'CormorantGaramond'),
        decoration: InputDecoration(
          hintText: 'Enter value...',
          hintStyle: TextStyle(
              color: ColorResources.whiteColor.withOpacity(0.3),
              fontFamily: 'CormorantGaramond'),
          enabledBorder: const UnderlineInputBorder(
              borderSide: BorderSide(color: ColorResources.borderColor)),
          focusedBorder: const UnderlineInputBorder(
              borderSide: BorderSide(color: ColorResources.primaryColor)),
        ),
        cursorColor: ColorResources.primaryColor,
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: Text('CANCEL',
              style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor.withOpacity(0.4),
                  letterSpacing: 1.5)),
        ),
        TextButton(
          onPressed: () {
            if (ctrl.text.trim().isNotEmpty) {
              onConfirm(ctrl.text.trim());
              Navigator.pop(context);
            }
          },
          child: const Text('ADD',
              style: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.primaryColor,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 1.5)),
        ),
      ],
    ),
  );
}