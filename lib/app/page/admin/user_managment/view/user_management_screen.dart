import 'package:aura/app/widgets/app_drop_down.dart';
import 'package:aura/app/widgets/custom_textform_lables.dart';
import 'package:aura/app/widgets/custom_textformfeild.dart';
import 'package:flutter/material.dart';
import 'package:get/get.dart';
import '../../../../theme/color/color.dart';
import '../../../../widgets/custom_appbar.dart';
import 'model/user_model.dart';



class ManageUsersScreen extends StatefulWidget {
  const ManageUsersScreen({super.key});

  @override
  State<ManageUsersScreen> createState() => _ManageUsersScreenState();
}

class _ManageUsersScreenState extends State<ManageUsersScreen> {
  // ── Data ─────────────────────────────────────────────────────────────────
  final List<StaffUser> _allUsers = [
    StaffUser(
      id: '1',
      username: 'Sarah Johnson',
      email: 'sarah@aura.com',
      phone: '+1 (555) 000-0001',
      role: UserRole.receptionist,
    ),
    StaffUser(
      id: '2',
      username: 'Dr. Marcus Lee',
      email: 'marcus@aura.com',
      phone: '+1 (555) 000-0002',
      role: UserRole.therapist,
    ),
    StaffUser(
      id: '3',
      username: 'Priya Nair',
      email: 'priya@aura.com',
      phone: '+1 (555) 000-0003',
      role: UserRole.therapist,
      status: UserStatus.inactive,
    ),
    StaffUser(
      id: '4',
      username: 'James Webb',
      email: 'james@aura.com',
      phone: '+1 (555) 000-0004',
      role: UserRole.receptionist,
    ),
    StaffUser(
      id: '5',
      username: 'Admin Root',
      email: 'admin@aura.com',
      phone: '+1 (555) 000-0000',
      role: UserRole.admin,
    ),
  ];

  // ── Filter state ──────────────────────────────────────────────────────────
  String _searchQuery = '';
  UserRole? _filterRole;

  // ── Derived ───────────────────────────────────────────────────────────────
  List<StaffUser> get _filtered {
    return _allUsers.where((u) {
      final q = _searchQuery.toLowerCase();
      final matchesSearch = q.isEmpty ||
          u.username.toLowerCase().contains(q) ||
          u.email.toLowerCase().contains(q);
      final matchesRole = _filterRole == null || u.role == _filterRole;
      return matchesSearch && matchesRole;
    }).toList();
  }

  // ── Actions ───────────────────────────────────────────────────────────────
  void _toggleStatus(StaffUser user) {
    setState(() {
      user.status = user.status == UserStatus.active
          ? UserStatus.inactive
          : UserStatus.active;
    });
  }

  void _deleteUser(String id) {
    setState(() => _allUsers.removeWhere((u) => u.id == id));
  }

  void _showDeleteSheet(StaffUser user) {
    showModalBottomSheet(
      context: context,
      backgroundColor: ColorResources.cardColor,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (_) => _DeleteConfirmSheet(
        user: user,
        onConfirm: () {
          _deleteUser(user.id);
          Navigator.pop(context);
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(
                '${user.username} has been removed',
                style: const TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.whiteColor,
                  fontSize: 14,
                ),
              ),
              backgroundColor: ColorResources.cardColor,
              behavior: SnackBarBehavior.floating,
              margin: const EdgeInsets.all(16),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
                side: BorderSide(
                  color: ColorResources.primaryColor.withOpacity(0.3),
                  width: 0.5,
                ),
              ),
              duration: const Duration(seconds: 3),
            ),
          );
        },
      ),
    );
  }

  void _showInviteUserDialog() {
    final nameController = TextEditingController();
    final emailController = TextEditingController();
    UserRole selectedRole = UserRole.therapist;

    Get.dialog(
      StatefulBuilder(
        builder: (context, setDialogState) {
          return Dialog(
            backgroundColor: ColorResources.blackColor,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(20),
              side: BorderSide(color: ColorResources.borderColor, width: 0.5),
            ),
            child: Padding(
              padding: const EdgeInsets.all(24),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                   Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'INVITE NEW USER',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor,
                          fontSize: 20,
                          fontWeight: FontWeight.w300,
                          letterSpacing: 2.0,
                        ),
                      ),
                      GestureDetector(
                        onTap: () => Get.back(),
                        child: Icon(Icons.close, color: ColorResources.liteTextColor.withOpacity(0.5), size: 20),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),
                  
                  // Name Field
                  const CustomLabel(text: 'FULL NAME'),
                  CustomTextField(
                    controller: nameController,
                    hint: 'e.g. Dr. Marcus Lee',
                  ),
                  const SizedBox(height: 16),

                  // Email Field
                  const CustomLabel(text: 'EMAIL ADDRESS'),
                  CustomTextField(
                    controller: emailController,
                    hint: 'e.g. marcus@aura.com',
                    keyboardType: TextInputType.emailAddress,
                  ),
                  const SizedBox(height: 16),

                  // Role Selection
                  const CustomLabel(text: 'SELECT ROLE'),
                  AppDropdown(
                    value: selectedRole.name,
                    items: UserRole.values.map((r) => r.name).toList(),
                    onChanged: (v) {
                      if (v != null) {
                        setDialogState(() {
                          selectedRole = UserRole.values.firstWhere((r) => r.name == v);
                        });
                      }
                    },
                  ),

                  const SizedBox(height: 32),

                  // Submit Button
                  GestureDetector(
                    onTap: () {
                      if (nameController.text.isNotEmpty && emailController.text.isNotEmpty) {
                        setState(() {
                          _allUsers.add(StaffUser(
                            id: DateTime.now().millisecondsSinceEpoch.toString(),
                            username: nameController.text,
                            email: emailController.text,
                            phone: '+1 (555) 000-0000', // Placeholder
                            role: selectedRole,
                          ));
                        });
                        Get.back();
                        Get.snackbar(
                          'Invitation Sent',
                          'Link has been sent to ${emailController.text}',
                          backgroundColor: ColorResources.cardColor,
                          colorText: ColorResources.whiteColor,
                          snackPosition: SnackPosition.BOTTOM,
                          margin: const EdgeInsets.all(16),
                          borderRadius: 12,
                          borderWidth: 0.5,
                          borderColor: ColorResources.primaryColor.withOpacity(0.3),
                        );
                      }
                    },
                    child: Container(
                      width: double.infinity,
                      height: 50,
                      decoration: BoxDecoration(
                        color: ColorResources.primaryColor,
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: const Center(
                        child: Text(
                          'SEND INVITATION',
                          style: TextStyle(
                            fontFamily: 'CormorantGaramond',
                            color: Colors.black,
                            fontSize: 14,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 2.0,
                          ),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          );
        }
      ),
    );
  }

  void _showResetPasswordDialog(StaffUser user) {
    final emailController = TextEditingController(text: user.email);

    Get.dialog(
      Dialog(
        backgroundColor: ColorResources.blackColor,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(20),
          side: BorderSide(color: ColorResources.borderColor, width: 0.5),
        ),
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'FORGOT PASSWORD',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 18,
                      fontWeight: FontWeight.w300,
                      letterSpacing: 2.0,
                    ),
                  ),
                  GestureDetector(
                    onTap: () => Get.back(),
                    child: Icon(Icons.close, color: ColorResources.liteTextColor.withOpacity(0.5), size: 20),
                  ),
                ],
              ),
              const SizedBox(height: 24),
              const CustomLabel(text: 'VERIFY EMAIL ADDRESS'),
              CustomTextField(
                controller: emailController,
                hint: 'e.g. marcus@aura.com',
                keyboardType: TextInputType.emailAddress,
              ),
              const SizedBox(height: 32),
              GestureDetector(
                onTap: () {
                  Get.back();
                  Get.snackbar(
                    'Reset Link Sent',
                    'A password reset link has been sent to ${emailController.text}',
                    backgroundColor: ColorResources.cardColor,
                    colorText: ColorResources.whiteColor,
                    snackPosition: SnackPosition.BOTTOM,
                    margin: const EdgeInsets.all(16),
                    borderRadius: 12,
                    borderWidth: 0.5,
                    borderColor: ColorResources.primaryColor.withOpacity(0.3),
                  );
                },
                child: Container(
                  width: double.infinity,
                  height: 50,
                  decoration: BoxDecoration(
                    color: ColorResources.primaryColor,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: const Center(
                    child: Text(
                      'SEND RESET LINK',
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: Colors.black,
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        letterSpacing: 2.0,
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  // ── Build ─────────────────────────────────────────────────────────────────
  @override
  Widget build(BuildContext context) {
    final filtered = _filtered;

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: const CustomAppBar(title: 'MANAGE USERS'),
      body: SafeArea(
        child: Column(
          children: [
            // ── Search & Filters ───────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 16, 20, 0),
              child: _SearchField(
                value: _searchQuery,
                selectedRole: _filterRole,
                onChanged: (v) => setState(() => _searchQuery = v),
                onRoleChanged: (role) => setState(() => _filterRole = role),
              ),
            ),

            const SizedBox(height: 24),

            // ── Invite Section ─────────────────────────────────────────────
            _buildInviteHeader(),

            const SizedBox(height: 32),

            // ── Count label ────────────────────────────────────────────────
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 20),
              child: Row(
                children: [
                  Text(
                    '${filtered.length} STAFF MEMBERS',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.4),
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.5,
                    ),
                  ),
                  const Spacer(),
                ],
              ),
            ),

            const SizedBox(height: 8),

            // ── List ───────────────────────────────────────────────────────
            Expanded(
              child: filtered.isEmpty
                  ? const _EmptyState()
                  : ListView.separated(
                      padding: const EdgeInsets.symmetric(horizontal: 20),
                      itemCount: filtered.length,
                      separatorBuilder: (_, __) => Divider(
                        color: ColorResources.borderColor.withOpacity(0.5),
                        height: 1,
                      ),
                      itemBuilder: (context, i) => _UserCard(
                        user: filtered[i],
                        onToggleStatus: () => _toggleStatus(filtered[i]),
                        onDelete: () => _showDeleteSheet(filtered[i]),
                        onEdit: () {
                          // TODO: Implement Edit
                        },
                        onSecurity: () => _showResetPasswordDialog(filtered[i]),
                      ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
  Widget _buildInviteHeader() {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 20),
      child: Container(
        padding: const EdgeInsets.all(20),
        decoration: BoxDecoration(
          color: ColorResources.cardColor,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(
            color: ColorResources.primaryColor.withOpacity(0.15),
            width: 0.5,
          ),
        ),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: ColorResources.primaryColor.withOpacity(0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.person_add_outlined,
                color: ColorResources.primaryColor,
                size: 20,
              ),
            ),
            const SizedBox(width: 16),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text(
                    'INVITE STAFF',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 14,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.5,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    'Add a new member to your team',
                    style: TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.liteTextColor.withOpacity(0.5),
                      fontSize: 12,
                    ),
                  ),
                ],
              ),
            ),
            GestureDetector(
              onTap: _showInviteUserDialog,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                decoration: BoxDecoration(
                  color: ColorResources.primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: ColorResources.primaryColor.withOpacity(0.5),
                    width: 0.5,
                  ),
                ),
                child: const Text(
                  'INVITE',
                  style: TextStyle(
                    fontFamily: 'CormorantGaramond',
                    color: ColorResources.primaryColor,
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    letterSpacing: 1.0,
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



class _SearchField extends StatelessWidget {
  final String value;
  final UserRole? selectedRole;
  final ValueChanged<String> onChanged;
  final ValueChanged<UserRole?> onRoleChanged;

  const _SearchField({
    required this.value,
    this.selectedRole,
    required this.onChanged,
    required this.onRoleChanged,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      height: 46,
      decoration: BoxDecoration(
        color: ColorResources.cardColor,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: ColorResources.borderColor, width: 0.5),
      ),
      child: Row(
        children: [
          Expanded(
            child: TextField(
              onChanged: onChanged,
              style: const TextStyle(
                fontFamily: 'CormorantGaramond',
                color: ColorResources.whiteColor,
                fontSize: 16,
              ),
              decoration: InputDecoration(
                hintText: 'Search by name or email…',
                hintStyle: TextStyle(
                  fontFamily: 'CormorantGaramond',
                  color: ColorResources.liteTextColor.withOpacity(0.35),
                  fontSize: 15,
                ),
                prefixIcon: Icon(
                  Icons.search,
                  color: ColorResources.liteTextColor.withOpacity(0.4),
                  size: 18,
                ),
                border: InputBorder.none,
                contentPadding: const EdgeInsets.symmetric(vertical: 12),
              ),
            ),
          ),
          if (value.isNotEmpty)
            GestureDetector(
              onTap: () => onChanged(''),
              child: Icon(
                Icons.close,
                color: ColorResources.liteTextColor.withOpacity(0.4),
                size: 16,
              ),
            ),
          const VerticalDivider(width: 1, indent: 10, endIndent: 10, color: ColorResources.borderColor),
          PopupMenuButton<UserRole?>(
            icon: Icon(
              Icons.tune_outlined,
              color: selectedRole != null ? ColorResources.primaryColor : ColorResources.liteTextColor.withOpacity(0.4),
              size: 18,
            ),
            offset: const Offset(0, 46),
            color: ColorResources.cardColor,
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(12),
              side: BorderSide(color: ColorResources.borderColor, width: 0.5),
            ),
            onSelected: onRoleChanged,
            itemBuilder: (context) => [
              const PopupMenuItem(
                value: null,
                child: Text('ALL ROLES', style: TextStyle(fontFamily: 'CormorantGaramond', color: ColorResources.liteTextColor, fontSize: 12)),
              ),
              ...UserRole.values.map((role) => PopupMenuItem(
                    value: role,
                    child: Text(
                      role.name.toUpperCase(),
                      style: TextStyle(
                        fontFamily: 'CormorantGaramond',
                        color: selectedRole == role ? ColorResources.primaryColor : ColorResources.whiteColor,
                        fontSize: 12,
                      ),
                    ),
                  )),
            ],
          ),
          const SizedBox(width: 4),
        ],
      ),
    );
  }
}



// ─────────────────────────────────────────────────────────────────────────────
//  USER CARD
// ─────────────────────────────────────────────────────────────────────────────

class _UserCard extends StatelessWidget {
  final StaffUser user;
  final VoidCallback onToggleStatus;
  final VoidCallback onDelete;
  final VoidCallback onEdit;
  final VoidCallback onSecurity;

  const _UserCard({
    required this.user,
    required this.onToggleStatus,
    required this.onDelete,
    required this.onEdit,
    required this.onSecurity,
  });

  @override
  Widget build(BuildContext context) {
    final isActive = user.status == UserStatus.active;


    return GestureDetector(
      onTap: onEdit,
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 20),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Info
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    user.username,
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.whiteColor,
                      fontSize: 17,
                      fontWeight: FontWeight.w400,
                      fontStyle: FontStyle.italic,
                      letterSpacing: 0.5,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    user.roleLabel.toUpperCase(),
                    style: const TextStyle(
                      fontFamily: 'CormorantGaramond',
                      color: ColorResources.primaryColor,
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      letterSpacing: 1.0,
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      Icon(Icons.email_outlined,
                          color: ColorResources.liteTextColor, size: 13),
                      const SizedBox(width: 6),
                      Text(
                        user.email,
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.liteTextColor,
                          fontSize: 12,
                          letterSpacing: 0.3,
                        ),
                      ),
                    ],
                  ),
                
                ],
              ),
            ),

            // Actions
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Transform.scale(
                  scale: 0.7,
                  alignment: Alignment.centerRight,
                  child: Switch(
                    value: isActive,
                    onChanged: (_) => onToggleStatus(),
                    activeColor: ColorResources.positiveColor,
                    activeTrackColor: ColorResources.positiveColor.withOpacity(0.15),
                    inactiveThumbColor: ColorResources.liteTextColor.withOpacity(0.35),
                    inactiveTrackColor: ColorResources.borderColor,
                  ),
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    _ActionIcon(
                      icon: Icons.lock_reset_outlined,
                      color: ColorResources.primaryColor,
                      onTap: onSecurity,
                    ),
                    const SizedBox(width: 16),
                    _ActionIcon(
                      icon: Icons.edit_outlined,
                      color: ColorResources.liteTextColor,
                      onTap: onEdit,
                    ),
                    const SizedBox(width: 16),
                    _ActionIcon(
                      icon: Icons.delete_outline,
                      color: const Color(0xFFEF5350),
                      size: 18,
                      onTap: onDelete,
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class _ActionIcon extends StatelessWidget {
  final IconData icon;
  final Color color;
  final VoidCallback onTap;
  final double size;

  const _ActionIcon({
    required this.icon,
    required this.color,
    required this.onTap,
    this.size = 20,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Icon(icon, color: color, size: size),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  EMPTY STATE
// ─────────────────────────────────────────────────────────────────────────────

class _EmptyState extends StatelessWidget {
  const _EmptyState();

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            Icons.person_search_outlined,
            size: 48,
            color: ColorResources.liteTextColor.withOpacity(0.2),
          ),
          const SizedBox(height: 16),
          Text(
            'No users found',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.4),
              fontSize: 18,
              fontWeight: FontWeight.w300,
              letterSpacing: 0.5,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Try adjusting your filters',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.25),
              fontSize: 13,
            ),
          ),
        ],
      ),
    );
  }
}

// ─────────────────────────────────────────────────────────────────────────────
//  DELETE CONFIRM BOTTOM SHEET
// ─────────────────────────────────────────────────────────────────────────────

class _DeleteConfirmSheet extends StatelessWidget {
  final StaffUser user;
  final VoidCallback onConfirm;

  const _DeleteConfirmSheet({required this.user, required this.onConfirm});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 36),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Center(
            child: Container(
              width: 36,
              height: 4,
              decoration: BoxDecoration(
                color: ColorResources.borderColor,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 24),
          Container(
            width: 44,
            height: 44,
            decoration: BoxDecoration(
              color: const Color(0xFFEF5350).withOpacity(0.1),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: const Color(0xFFEF5350).withOpacity(0.25),
                width: 0.5,
              ),
            ),
            child: const Icon(Icons.delete_outline, color: Color(0xFFEF5350), size: 20),
          ),
          const SizedBox(height: 16),
          const Text(
            'Remove user?',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.whiteColor,
              fontSize: 22,
              fontWeight: FontWeight.w300,
            ),
          ),
          const SizedBox(height: 8),
          Text(
            '${user.username} will be permanently removed from the system. This action cannot be undone.',
            style: TextStyle(
              fontFamily: 'CormorantGaramond',
              color: ColorResources.liteTextColor.withOpacity(0.55),
              fontSize: 14,
              height: 1.5,
            ),
          ),
          const SizedBox(height: 28),
          Row(
            children: [
              Expanded(
                child: GestureDetector(
                  onTap: () => Navigator.pop(context),
                  child: Container(
                    height: 48,
                    decoration: BoxDecoration(
                      color: ColorResources.cardColor,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: ColorResources.borderColor, width: 0.5),
                    ),
                    child: const Center(
                      child: Text(
                        'CANCEL',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: ColorResources.whiteColor,
                          fontSize: 14,
                          fontWeight: FontWeight.w500,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: GestureDetector(
                  onTap: onConfirm,
                  child: Container(
                    height: 48,
                    decoration: BoxDecoration(
                      color: const Color(0xFFEF5350).withOpacity(0.12),
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(
                        color: const Color(0xFFEF5350).withOpacity(0.4),
                        width: 0.5,
                      ),
                    ),
                    child: const Center(
                      child: Text(
                        'REMOVE',
                        style: TextStyle(
                          fontFamily: 'CormorantGaramond',
                          color: Color(0xFFEF5350),
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          letterSpacing: 1.5,
                        ),
                      ),
                    ),
                  ),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}